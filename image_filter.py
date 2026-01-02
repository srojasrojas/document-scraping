"""
Módulo para filtrar imágenes extraídas usando OCR.
Descarta imágenes decorativas (banners, logos, iconos) que no contienen
información valiosa para análisis.
"""

import json
from pathlib import Path
from typing import List, Tuple, Optional
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
        
        # Obtener configuración de filtrado (con valores por defecto)
        filter_config = self.config.extraction.get('image_filter', {})
        
        # Umbral mínimo de caracteres para considerar texto significativo
        self.min_chars = filter_config.get('min_chars', 10)
        
        # Umbral mínimo de dígitos (los gráficos suelen tener números)
        self.min_digits = filter_config.get('min_digits', 2)
        
        # Tamaño mínimo en píxeles (ancho o alto)
        self.min_dimension = filter_config.get('min_dimension', 100)
        
        # Área mínima en píxeles cuadrados
        self.min_area = filter_config.get('min_area', 10000)
        
        # Si tiene números, reducir el umbral de caracteres
        self.chars_with_numbers_multiplier = filter_config.get('chars_with_numbers_multiplier', 0.5)
        
        # Idiomas para OCR (español e inglés por defecto)
        self.ocr_lang = filter_config.get('ocr_lang', 'spa+eng')
        
        # Modo verbose para debugging
        self.verbose = filter_config.get('verbose', True)
        
        print(f"✓ Filtro de imágenes inicializado")
        print(f"  → Mínimo caracteres: {self.min_chars}")
        print(f"  → Mínimo dígitos: {self.min_digits}")
        print(f"  → Dimensión mínima: {self.min_dimension}px")
        print(f"  → Área mínima: {self.min_area}px²")
    
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
            
            # Calcular confianza promedio
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return OCRResult(
                text=text,
                char_count=char_count,
                digit_count=digit_count,
                word_count=word_count,
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
        
        Retorna:
            - (True/False, razón, resultado_ocr)
        """
        # Paso 1: Verificar dimensiones
        dims_ok, dims_reason = self.check_dimensions(image_data)
        if not dims_ok:
            return False, dims_reason, None
        
        # Paso 2: Realizar OCR
        ocr_result = self.analyze_image_ocr(image_data.path)
        
        # Paso 3: Evaluar contenido
        # Caso especial: si tiene suficientes números, probablemente es un gráfico
        if ocr_result.digit_count >= self.min_digits:
            # Con números, reducimos el umbral de caracteres
            adjusted_min_chars = int(self.min_chars * self.chars_with_numbers_multiplier)
            if ocr_result.char_count >= adjusted_min_chars:
                return True, f"Gráfico/datos ({ocr_result.digit_count} números, {ocr_result.char_count} chars)", ocr_result
        
        # Caso general: verificar cantidad de texto
        if ocr_result.char_count >= self.min_chars:
            return True, f"Texto suficiente ({ocr_result.char_count} chars)", ocr_result
        
        # No cumple criterios
        reason = f"Poco contenido ({ocr_result.char_count} chars, {ocr_result.digit_count} números)"
        return False, reason, ocr_result
    
    def filter_images(self, images: List[ImageData]) -> Tuple[List[ImageData], List[ImageData]]:
        """
        Filtra una lista de imágenes, separando las valiosas de las descartables.
        
        Retorna:
            - (imágenes_valiosas, imágenes_descartadas)
        """
        valuable = []
        discarded = []
        
        print(f"\n🔍 Filtrando {len(images)} imágenes con OCR...")
        
        for img in images:
            is_valuable, reason, ocr_result = self.is_valuable_image(img)
            
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
