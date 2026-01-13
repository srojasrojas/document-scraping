"""
Módulo para filtrar imágenes extraídas usando OCR.
Descarta imágenes decorativas (banners, logos, iconos) que no contienen
información valiosa para análisis.
"""

import json
import os
import platform
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from PIL import Image
import pytesseract
import re

from models import ImageData, Config


@dataclass
class OCRResult:
    """Resultado del análisis OCR de una imagen"""
    text: str
    char_count: int
    digit_count: int
    word_count: int
    useful_word_count: int  # Palabras excluyendo las ignoradas
    has_numbers: bool
    confidence_score: float


class ImageFilter:
    """
    Filtra imágenes usando OCR para determinar si contienen información valiosa.
    
    Criterios para considerar una imagen como valiosa:
    1. Contiene un mínimo de caracteres (texto legible)
    2. Contiene números (importante para gráficos/charts)
    3. Tiene un tamaño mínimo (descarta iconos pequeños)
    4. Tiene una relación de aspecto razonable
    """
    
    def __init__(self, config_path: str = "config.json"):
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        self.config = Config(**config_data)
        
        # Almacenar resultados de OCR para uso posterior (ej: detección de composites)
        self._ocr_results: Dict[str, int] = {}
        
        # Obtener configuración de filtrado (con valores por defecto)
        filter_config = self.config.extraction.get('image_filter', {})
        
        # Configurar ruta de Tesseract
        self._setup_tesseract(filter_config)
        
        # Umbral mínimo de caracteres para considerar texto significativo
        self.min_chars = filter_config.get('min_chars', 10)
        
        # Umbral mínimo de dígitos (los gráficos suelen tener números)
        self.min_digits = filter_config.get('min_digits', 2)
        
        # Mínimo de palabras (logos tienen pocas palabras)
        self.min_words = filter_config.get('min_words', 5)
        
        # Densidad mínima de texto (caracteres por 10000 px²)
        # Logos tienen baja densidad, tablas/gráficos tienen alta densidad
        self.min_text_density = filter_config.get('min_text_density', 5)
        
        # Tamaño mínimo en píxeles (ancho o alto)
        self.min_dimension = filter_config.get('min_dimension', 100)
        
        # Área mínima en píxeles cuadrados
        self.min_area = filter_config.get('min_area', 10000)
        
        # Si tiene números, reducir el umbral de caracteres
        self.chars_with_numbers_multiplier = filter_config.get('chars_with_numbers_multiplier', 0.5)
        
        # Requerir números para considerar imagen valiosa (estricto)
        self.require_numbers = filter_config.get('require_numbers', False)
        
        # Palabras a ignorar (nombres de empresas, eslóganes) - no cuentan para el mínimo
        self.ignore_words = set(w.lower() for w in filter_config.get('ignore_words', [
            'afp', 'habitat', 'cuprum', 'capital', 'provida', 'planvital', 'modelo', 'uno',
            'seguridad', 'confianza', 'compañía', 'principal', 'una', 'logo', 'marca',
            'chile', 'www', 'com', 'cl', 'http', 'https'
        ]))
        
        # Idiomas para OCR (español e inglés por defecto)
        self.ocr_lang = filter_config.get('ocr_lang', 'spa+eng')
        
        # Modo verbose para debugging
        self.verbose = filter_config.get('verbose', True)
        
        print(f"✓ Filtro de imágenes inicializado")
        print(f"  → Mínimo caracteres: {self.min_chars}")
        print(f"  → Mínimo palabras: {self.min_words}")
        print(f"  → Mínimo dígitos: {self.min_digits}")
        print(f"  → Densidad mínima: {self.min_text_density} chars/10Kpx²")
        print(f"  → Dimensión mínima: {self.min_dimension}px")
        print(f"  → Área mínima: {self.min_area}px²")
        if self.require_numbers:
            print(f"  → Requiere números: SÍ")
    
    def _setup_tesseract(self, filter_config: dict):
        """
        Configura la ruta del ejecutable de Tesseract.
        Intenta detección automática en Windows si no está configurado.
        """
        # Verificar si hay una ruta configurada
        tesseract_cmd = filter_config.get('tesseract_cmd')
        
        if tesseract_cmd and Path(tesseract_cmd).exists():
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            print(f"  → Tesseract: {tesseract_cmd}")
            return
        
        # Detectar automáticamente en Windows
        if platform.system() == 'Windows':
            possible_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'C:\Tesseract-OCR\tesseract.exe',
                os.path.expanduser(r'~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'),
            ]
            
            for path in possible_paths:
                if Path(path).exists():
                    pytesseract.pytesseract.tesseract_cmd = path
                    print(f"  → Tesseract detectado: {path}")
                    return
        
        # Si no se encontró, intentar usar el PATH del sistema
        print(f"  → Tesseract: usando PATH del sistema")
        print(f"     Si hay errores, configura 'tesseract_cmd' en config.json")
    
    def analyze_image_ocr(self, image_path: str) -> OCRResult:
        """
        Realiza OCR en una imagen y extrae métricas del texto detectado.
        """
        try:
            img = Image.open(image_path)
            
            # Configuración de pytesseract para mejor detección
            custom_config = r'--oem 3 --psm 6'
            
            # Obtener texto con datos de confianza
            data = pytesseract.image_to_data(
                img, 
                lang=self.ocr_lang,
                config=custom_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Extraer texto limpio
            text_parts = []
            confidences = []
            
            for i, word in enumerate(data['text']):
                if word.strip():
                    text_parts.append(word)
                    conf = data['conf'][i]
                    if conf != -1:  # -1 significa sin confianza
                        confidences.append(conf)
            
            text = ' '.join(text_parts)
            
            # Calcular métricas
            char_count = len(re.sub(r'\s', '', text))  # Sin espacios
            digit_count = len(re.findall(r'\d', text))
            word_count = len(text_parts)
            has_numbers = digit_count > 0
            
            # Contar palabras útiles (excluyendo las ignoradas y palabras muy cortas)
            useful_words = [w for w in text_parts 
                           if len(w) > 2 and w.lower() not in self.ignore_words]
            useful_word_count = len(useful_words)
            
            # Calcular confianza promedio
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return OCRResult(
                text=text,
                char_count=char_count,
                digit_count=digit_count,
                word_count=word_count,
                useful_word_count=useful_word_count,
                has_numbers=has_numbers,
                confidence_score=avg_confidence
            )
            
        except Exception as e:
            if self.verbose:
                print(f"  ⚠️  Error en OCR para {image_path}: {e}")
            return OCRResult(
                text="",
                char_count=0,
                digit_count=0,
                word_count=0,
                useful_word_count=0,
                has_numbers=False,
                confidence_score=0
            )
    
    def check_dimensions(self, image_data: ImageData) -> Tuple[bool, str]:
        """
        Verifica si las dimensiones de la imagen son adecuadas.
        Retorna (es_válida, razón)
        """
        # Verificar dimensión mínima
        if image_data.width < self.min_dimension and image_data.height < self.min_dimension:
            return False, f"Muy pequeña ({image_data.width}x{image_data.height})"
        
        # Verificar área mínima
        area = image_data.width * image_data.height
        if area < self.min_area:
            return False, f"Área insuficiente ({area}px²)"
        
        # Verificar proporciones extremas (probablemente banners/líneas)
        aspect_ratio = max(image_data.width, image_data.height) / max(1, min(image_data.width, image_data.height))
        if aspect_ratio > 10:
            return False, f"Proporción extrema ({aspect_ratio:.1f}:1)"
        
        return True, "OK"
    
    def is_valuable_image(self, image_data: ImageData) -> Tuple[bool, str, Optional[OCRResult]]:
        """
        Determina si una imagen contiene información valiosa para análisis.
        
        Criterios más estrictos para filtrar logos y banners:
        1. Debe tener suficientes números (gráficos/tablas siempre tienen datos)
        2. O tener alta densidad de texto (muchas palabras útiles por área)
        3. Las palabras de marca/empresa no cuentan
        
        Retorna:
            - (True/False, razón, resultado_ocr)
        """
        # Paso 1: Verificar dimensiones
        dims_ok, dims_reason = self.check_dimensions(image_data)
        if not dims_ok:
            return False, dims_reason, None
        
        # Paso 2: Realizar OCR
        ocr_result = self.analyze_image_ocr(image_data.path)
        
        # Calcular área y densidad de texto
        area = image_data.width * image_data.height
        text_density = (ocr_result.char_count * 10000) / area if area > 0 else 0
        
        # Paso 3: Evaluar contenido con criterios más estrictos
        
        # Criterio A: Tiene suficientes números (esencial para gráficos/tablas)
        has_good_numbers = ocr_result.digit_count >= self.min_digits
        
        # Criterio B: Tiene suficientes palabras útiles (no son solo nombres de empresa)
        has_enough_words = ocr_result.useful_word_count >= self.min_words
        
        # Criterio C: Tiene buena densidad de texto (no es un logo con mucho espacio vacío)
        has_good_density = text_density >= self.min_text_density
        
        # Lógica de decisión:
        
        # Si require_numbers está activo, es obligatorio tener números
        if self.require_numbers and not has_good_numbers:
            return False, f"Sin números ({ocr_result.digit_count} dígitos)", ocr_result
        
        # Caso ideal: tiene números Y buena densidad -> probablemente gráfico/tabla
        if has_good_numbers and has_good_density:
            return True, f"Gráfico/tabla ({ocr_result.digit_count} núms, densidad={text_density:.1f})", ocr_result
        
        # Caso secundario: muchas palabras útiles Y buena densidad -> probablemente contenido textual valioso
        if has_enough_words and has_good_density:
            return True, f"Contenido denso ({ocr_result.useful_word_count} palabras, densidad={text_density:.1f})", ocr_result
        
        # Caso con números pero baja densidad: aún podría ser útil si hay suficientes
        if ocr_result.digit_count >= self.min_digits * 2:  # El doble del mínimo
            return True, f"Datos numéricos ({ocr_result.digit_count} números)", ocr_result
        
        # No cumple criterios - probablemente logo/banner
        reasons = []
        if not has_good_numbers:
            reasons.append(f"{ocr_result.digit_count} núms")
        if not has_enough_words:
            reasons.append(f"{ocr_result.useful_word_count} palabras útiles")
        if not has_good_density:
            reasons.append(f"densidad={text_density:.1f}")
        
        return False, f"Probable logo/banner ({', '.join(reasons)})", ocr_result
    
    def filter_images(self, images: List[ImageData]) -> Tuple[List[ImageData], List[ImageData]]:
        """
        Filtra una lista de imágenes, separando las valiosas de las descartables.
        
        Retorna:
            - (imágenes_valiosas, imágenes_descartadas)
        """
        valuable = []
        discarded = []
        
        # Limpiar resultados de OCR anteriores
        self._ocr_results = {}
        
        print(f"\n🔍 Filtrando {len(images)} imágenes con OCR...")
        
        for img in images:
            is_valuable, reason, ocr_result = self.is_valuable_image(img)
            
            # Guardar resultado de OCR para uso posterior
            if ocr_result:
                self._ocr_results[img.filename] = ocr_result.digit_count
            
            if is_valuable:
                valuable.append(img)
                if self.verbose:
                    print(f"  ✓ {img.filename}: {reason}")
            else:
                discarded.append(img)
                if self.verbose:
                    print(f"  ✗ {img.filename}: {reason}")
        
        print(f"\n📊 Resultado del filtrado:")
        print(f"   ✓ Imágenes valiosas: {len(valuable)}")
        print(f"   ✗ Imágenes descartadas: {len(discarded)}")
        
        return valuable, discarded
    
    def get_ocr_results(self) -> Dict[str, int]:
        """
        Retorna los resultados de OCR del último filtrado.
        
        Returns:
            Dict con {filename: digit_count} para cada imagen procesada
        """
        return self._ocr_results.copy()


if __name__ == "__main__":
    # Ejemplo de uso
    filter = ImageFilter()
    
    # Probar con una imagen de ejemplo
    test_image = ImageData(
        filename="test.png",
        page_number=1,
        path="output/images/test.png",
        width=800,
        height=600
    )
    
    # Verificar si existe
    if Path(test_image.path).exists():
        is_valuable, reason, ocr = filter.is_valuable_image(test_image)
        print(f"\nResultado: {'Valiosa' if is_valuable else 'Descartada'}")
        print(f"Razón: {reason}")
        if ocr:
            print(f"Texto detectado: {ocr.text[:200]}...")
    else:
        print("No hay imagen de prueba disponible")
