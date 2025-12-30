import json
import base64
from pathlib import Path
from typing import List
from pydantic_ai import Agent
from models import ChartData, ImageData, Config, TextData
from pydantic_ai.models.anthropic import AnthropicModel


class DocumentAnalyzer:
    def __init__(self, config_path: str = "config.json"):
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        self.config = Config(**config_data)
        
        # Crear agente con modelo de Anthropic
        model = AnthropicModel(
            self.config.analysis['model'],
            api_key=None  # Se maneja automáticamente en claude.ai
        )
        
        self.chart_agent = Agent(
            model=model,
            result_type=ChartData,
            system_prompt=self.config.prompts['chart_analysis']
        )
    
    def analyze_image(self, image_path: str) -> ChartData:
        """Analiza una imagen (gráfico) usando Claude"""
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Determinar el tipo MIME
        ext = Path(image_path).suffix.lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        media_type = mime_types.get(ext, 'image/png')
        
        # Analizar con el agente
        result = self.chart_agent.run_sync(
            f"Analiza este gráfico y extrae toda la información relevante.",
            message_history=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data
                        }
                    }
                ]
            }]
        )
        
        return result.data
    
    def analyze_all_images(self, images: List[ImageData]) -> List[ChartData]:
        """Analiza todas las imágenes extraídas"""
        results = []
        for img in images:
            try:
                print(f"Analizando {img.filename}...")
                chart_data = self.analyze_image(img.path)
                results.append(chart_data)
            except Exception as e:
                print(f"Error analizando {img.filename}: {e}")
        
        return results
    
    def extract_text_metrics(self, text_data: List[TextData]) -> List[TextData]:
        """Extrae métricas del texto usando expresiones regulares simples"""
        import re
        
        for text in text_data:
            content = text.content
            
            # Buscar porcentajes
            percentages = re.findall(r'(\d+(?:\.\d+)?)\s*%', content)
            text.percentages = [float(p) for p in percentages]
            
            # Buscar fechas (formato simple)
            dates = re.findall(r'\d{1,2}/\d{1,2}/\d{2,4}', content)
            text.dates = dates
            
            # Palabras clave simples (palabras en mayúsculas o números grandes)
            keywords = re.findall(r'\b[A-Z]{2,}\b|\b\d{1,3}(?:,\d{3})+\b', content)
            text.keywords = keywords[:10]  # Top 10
        
        return text_data


if __name__ == "__main__":
    # Ejemplo de uso
    analyzer = DocumentAnalyzer()
    
    # Simular análisis de una imagen
    img = ImageData(
        filename="chart.png",
        page_number=1,
        path="output/images/chart.png",
        width=800,
        height=600
    )
    
    result = analyzer.analyze_image(img.path)
    print(result.model_dump_json(indent=2))
