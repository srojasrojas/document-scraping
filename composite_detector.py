"""
Módulo para detectar y manejar gráficos compuestos.

Un gráfico compuesto es aquel donde:
- Los elementos visuales (barras, líneas, áreas) están como imagen
- Los valores numéricos y etiquetas están como texto renderizado separado

Este módulo:
1. Detecta imágenes que probablemente son gráficos (por dimensiones y posición)
2. Extrae texto con coordenadas de la página
3. Encuentra texto cercano/superpuesto a cada imagen
4. Enriquece ImageData con el contexto textual
"""

import json
import re
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

import fitz  # PyMuPDF

from models import ImageData, Config


@dataclass
class TextBlock:
    """Bloque de texto con su posición en la página"""
    text: str
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    page_number: int


@dataclass
class CompositeChartInfo:
    """Información de un gráfico compuesto detectado"""
    image: ImageData
    nearby_text: str
    overlapping_text: str
    confidence: float  # 0-1, qué tan probable es que sea un gráfico compuesto


class CompositeChartDetector:
    """
    Detecta gráficos donde la imagen contiene los elementos visuales
    pero los números/etiquetas están como texto separado en el PDF.
    """
    
    def __init__(self, config_path: str = "config.json"):
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        self.config = Config(**config_data)
        
        # Configuración específica para detección de composites
        composite_config = self.config.extraction.get('composite_detection', {})
        
        # Margen para buscar texto cercano (en puntos, 72 puntos = 1 pulgada)
        self.proximity_margin = composite_config.get('proximity_margin', 50)
        
        # Tamaño mínimo para considerar una imagen como potencial gráfico
        self.min_chart_width = composite_config.get('min_chart_width', 200)
        self.min_chart_height = composite_config.get('min_chart_height', 150)
        
        # Proporción mínima de la página que debe ocupar (evita iconos)
        self.min_page_ratio = composite_config.get('min_page_ratio', 0.1)
        
        # Mínimo de números encontrados en texto cercano para confirmar composite
        self.min_nearby_numbers = composite_config.get('min_nearby_numbers', 3)
        
        # Si el OCR de la imagen tiene pocos números, es candidato a composite
        self.ocr_number_threshold = composite_config.get('ocr_number_threshold', 2)
        
        # Verbose mode
        self.verbose = composite_config.get('verbose', True)
        
        if self.verbose:
            print(f"✓ Detector de gráficos compuestos inicializado")
            print(f"  → Margen de proximidad: {self.proximity_margin}pt")
            print(f"  → Tamaño mínimo gráfico: {self.min_chart_width}x{self.min_chart_height}")
    
    def extract_text_blocks(self, pdf_path: str) -> Dict[int, List[TextBlock]]:
        """
        Extrae todos los bloques de texto de un PDF con sus coordenadas.
        
        Returns:
            Dict mapeando número de página a lista de TextBlocks
        """
        doc = fitz.open(pdf_path)
        text_blocks_by_page: Dict[int, List[TextBlock]] = {}
        
        for page_num, page in enumerate(doc, start=1):
            blocks = []
            
            # Obtener bloques de texto con posiciones
            # Usamos "dict" para obtener información detallada
            text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
            
            for block in text_dict.get("blocks", []):
                if block.get("type") == 0:  # Tipo 0 = texto
                    bbox = block.get("bbox", (0, 0, 0, 0))
                    
                    # Extraer texto de todas las líneas del bloque
                    text_parts = []
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text_parts.append(span.get("text", ""))
                    
                    text = " ".join(text_parts).strip()
                    
                    if text:
                        blocks.append(TextBlock(
                            text=text,
                            bbox=bbox,
                            page_number=page_num
                        ))
            
            text_blocks_by_page[page_num] = blocks
        
        doc.close()
        return text_blocks_by_page
    
    def extract_image_positions(self, pdf_path: str) -> Dict[int, List[Tuple[int, Tuple[float, float, float, float]]]]:
        """
        Extrae las posiciones (bounding boxes) de las imágenes en cada página.
        
        Returns:
            Dict mapeando número de página a lista de (xref, bbox)
        """
        doc = fitz.open(pdf_path)
        image_positions: Dict[int, List[Tuple[int, Tuple[float, float, float, float]]]] = {}
        
        for page_num, page in enumerate(doc, start=1):
            positions = []
            
            # Obtener imágenes con sus posiciones
            image_list = page.get_images(full=True)
            
            for img_info in image_list:
                xref = img_info[0]
                
                # Buscar el rectángulo de la imagen en la página
                # Esto requiere buscar en el contenido de la página
                for img_rect in page.get_image_rects(xref):
                    bbox = (img_rect.x0, img_rect.y0, img_rect.x1, img_rect.y1)
                    positions.append((xref, bbox))
            
            image_positions[page_num] = positions
        
        doc.close()
        return image_positions
    
    def _boxes_overlap(self, box1: Tuple[float, float, float, float], 
                       box2: Tuple[float, float, float, float]) -> bool:
        """Verifica si dos bounding boxes se superponen"""
        x0_1, y0_1, x1_1, y1_1 = box1
        x0_2, y0_2, x1_2, y1_2 = box2
        
        return not (x1_1 < x0_2 or x1_2 < x0_1 or y1_1 < y0_2 or y1_2 < y0_1)
    
    def _boxes_nearby(self, box1: Tuple[float, float, float, float], 
                      box2: Tuple[float, float, float, float],
                      margin: float) -> bool:
        """Verifica si dos bounding boxes están cerca (dentro del margen)"""
        x0_1, y0_1, x1_1, y1_1 = box1
        x0_2, y0_2, x1_2, y1_2 = box2
        
        # Expandir box1 con el margen
        expanded_box1 = (
            x0_1 - margin,
            y0_1 - margin,
            x1_1 + margin,
            y1_1 + margin
        )
        
        return self._boxes_overlap(expanded_box1, box2)
    
    def _count_numbers_in_text(self, text: str) -> int:
        """Cuenta la cantidad de números en un texto"""
        # Buscar números (enteros, decimales, porcentajes)
        numbers = re.findall(r'\d+(?:[.,]\d+)?%?', text)
        return len(numbers)
    
    def _is_potential_chart(self, image: ImageData, page_width: float, page_height: float) -> bool:
        """
        Determina si una imagen podría ser un gráfico basándose en sus dimensiones.
        """
        # Verificar tamaño mínimo
        if image.width < self.min_chart_width or image.height < self.min_chart_height:
            return False
        
        # Verificar que ocupa una porción significativa de la página
        # Nota: las dimensiones de ImageData están en píxeles de la imagen original,
        # pero podemos usar la proporción como heurística
        if image.bbox:
            x0, y0, x1, y1 = image.bbox
            img_width = x1 - x0
            img_height = y1 - y0
            page_area = page_width * page_height
            img_area = img_width * img_height
            
            if page_area > 0 and (img_area / page_area) < self.min_page_ratio:
                return False
        
        return True
    
    def find_context_for_image(self, image: ImageData, 
                               text_blocks: List[TextBlock],
                               page_width: float = 612,  # Letter width in points
                               page_height: float = 792) -> Tuple[str, str, float]:
        """
        Encuentra el texto cercano y superpuesto a una imagen.
        
        Returns:
            (texto_cercano, texto_superpuesto, confidence)
        """
        if not image.bbox:
            return "", "", 0.0
        
        overlapping_texts = []
        nearby_texts = []
        
        img_bbox = tuple(image.bbox)
        
        for block in text_blocks:
            if self._boxes_overlap(img_bbox, block.bbox):
                overlapping_texts.append(block.text)
            elif self._boxes_nearby(img_bbox, block.bbox, self.proximity_margin):
                nearby_texts.append(block.text)
        
        overlapping_text = " ".join(overlapping_texts)
        nearby_text = " ".join(nearby_texts)
        
        # Calcular confianza basada en la cantidad de números encontrados
        all_context_text = f"{overlapping_text} {nearby_text}"
        num_count = self._count_numbers_in_text(all_context_text)
        
        # Confianza alta si hay muchos números en el contexto
        if num_count >= self.min_nearby_numbers * 2:
            confidence = 0.9
        elif num_count >= self.min_nearby_numbers:
            confidence = 0.7
        elif num_count >= 1:
            confidence = 0.4
        else:
            confidence = 0.1
        
        return nearby_text, overlapping_text, confidence
    
    def enrich_images_with_context(self, 
                                   images: List[ImageData], 
                                   pdf_path: str,
                                   ocr_results: Dict[str, int] = None) -> List[ImageData]:
        """
        Enriquece las imágenes con contexto textual del PDF.
        
        Args:
            images: Lista de ImageData a enriquecer
            pdf_path: Ruta al PDF original
            ocr_results: Dict opcional con {filename: digit_count} del OCR previo
        
        Returns:
            Lista de ImageData enriquecidas con context_text e is_composite
        """
        if not images:
            return images
        
        if self.verbose:
            print(f"\n🔍 Buscando gráficos compuestos en {len(images)} imágenes...")
        
        # Extraer texto con posiciones
        text_blocks_by_page = self.extract_text_blocks(pdf_path)
        
        # Extraer posiciones de imágenes
        image_positions = self.extract_image_positions(pdf_path)
        
        # Obtener dimensiones de página del primer documento
        doc = fitz.open(pdf_path)
        page_width = doc[0].rect.width if doc else 612
        page_height = doc[0].rect.height if doc else 792
        doc.close()
        
        # Crear mapeo de xref a posición para cada página
        xref_to_bbox: Dict[int, Dict[int, Tuple[float, float, float, float]]] = {}
        for page_num, positions in image_positions.items():
            xref_to_bbox[page_num] = {xref: bbox for xref, bbox in positions}
        
        enriched_images = []
        composite_count = 0
        
        for img in images:
            # Obtener bbox si no está ya establecido
            if not img.bbox:
                page_positions = xref_to_bbox.get(img.page_number, {})
                # Intentar encontrar la imagen por índice (heurística)
                img_idx = int(re.search(r'img(\d+)', img.filename).group(1)) if re.search(r'img(\d+)', img.filename) else 0
                
                if page_positions:
                    # Tomar la posición correspondiente al índice
                    positions_list = list(page_positions.values())
                    if img_idx < len(positions_list):
                        img.bbox = list(positions_list[img_idx])
            
            # Buscar contexto textual
            text_blocks = text_blocks_by_page.get(img.page_number, [])
            nearby_text, overlapping_text, confidence = self.find_context_for_image(
                img, text_blocks, page_width, page_height
            )
            
            # Determinar si es un gráfico compuesto
            is_composite = False
            context_text = ""
            
            # Criterio 1: La imagen tiene el tamaño de un gráfico potencial
            is_potential = self._is_potential_chart(img, page_width, page_height)
            
            # Criterio 2: Hay números significativos en el contexto
            total_context = f"{overlapping_text} {nearby_text}"
            context_numbers = self._count_numbers_in_text(total_context)
            
            # Criterio 3 (opcional): El OCR de la imagen detectó pocos números
            ocr_numbers = 0
            if ocr_results and img.filename in ocr_results:
                ocr_numbers = ocr_results[img.filename]
            
            # Decisión: Es composite si parece gráfico Y tiene contexto numérico significativo
            if is_potential and context_numbers >= self.min_nearby_numbers:
                # Si el OCR de la imagen tiene pocos números, es más probable que sea composite
                if ocr_numbers < self.ocr_number_threshold:
                    is_composite = True
                    confidence = min(0.95, confidence + 0.2)
                elif context_numbers >= self.min_nearby_numbers * 2:
                    # Aún así podría ser composite si hay muchos números en contexto
                    is_composite = True
            
            if is_composite or (overlapping_text.strip() or nearby_text.strip()):
                # Combinar texto superpuesto y cercano
                context_parts = []
                if overlapping_text.strip():
                    context_parts.append(f"[SOBRE IMAGEN]: {overlapping_text.strip()}")
                if nearby_text.strip():
                    context_parts.append(f"[CERCA DE IMAGEN]: {nearby_text.strip()}")
                
                context_text = "\n".join(context_parts)
                img.context_text = context_text
                img.is_composite = is_composite
                
                if is_composite:
                    composite_count += 1
                    if self.verbose:
                        print(f"  📊 {img.filename}: Gráfico compuesto detectado (confianza: {confidence:.0%})")
                        print(f"      → {context_numbers} números en contexto, {ocr_numbers} en imagen")
            
            enriched_images.append(img)
        
        if self.verbose:
            print(f"\n✓ Resultado: {composite_count} gráficos compuestos detectados de {len(images)} imágenes")
        
        return enriched_images


def detect_composite_charts(pdf_path: str, images: List[ImageData], 
                           config_path: str = "config.json",
                           ocr_results: Dict[str, int] = None) -> List[ImageData]:
    """
    Función de conveniencia para detectar y enriquecer gráficos compuestos.
    
    Args:
        pdf_path: Ruta al archivo PDF
        images: Lista de ImageData extraídas
        config_path: Ruta al archivo de configuración
        ocr_results: Dict opcional con resultados de OCR {filename: digit_count}
    
    Returns:
        Lista de ImageData enriquecidas
    """
    detector = CompositeChartDetector(config_path)
    return detector.enrich_images_with_context(images, pdf_path, ocr_results)


if __name__ == "__main__":
    # Ejemplo de uso
    from models import ImageData
    
    print("=== Test del Detector de Gráficos Compuestos ===\n")
    
    # Crear una imagen de prueba
    test_image = ImageData(
        filename="page1_img0.png",
        page_number=1,
        path="output/images/page1_img0.png",
        width=800,
        height=400
    )
    
    # Probar con un PDF de ejemplo (si existe)
    test_pdf = "test.pdf"
    if Path(test_pdf).exists():
        detector = CompositeChartDetector()
        enriched = detector.enrich_images_with_context([test_image], test_pdf)
        
        for img in enriched:
            print(f"\nImagen: {img.filename}")
            print(f"  Compuesto: {img.is_composite}")
            if img.context_text:
                print(f"  Contexto: {img.context_text[:200]}...")
    else:
        print(f"No se encontró {test_pdf} para pruebas")
        print("Creando detector para verificar configuración...")
        detector = CompositeChartDetector()
        print("\n✓ Detector creado exitosamente")
