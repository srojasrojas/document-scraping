import json
import os
import base64
from pathlib import Path
from typing import List
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIChatModel
from models import ChartData, ImageData, Config, TextData, TextAnalysis


class DocumentAnalyzer:
    def __init__(self, config_path: str = "config.json"):
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        self.config = Config(**config_data)
        
        # Obtener configuración del proveedor
        provider = self.config.analysis.get('provider', 'anthropic').lower()
        model_name = self.config.analysis['model']
        
        # Crear modelo según el proveedor
        if provider == 'anthropic':
            model = self._create_anthropic_model(model_name)
        elif provider == 'openai':
            model = self._create_openai_model(model_name)
        else:
            raise ValueError(f"Proveedor no soportado: {provider}. Use 'anthropic' o 'openai'")
        
        # Cargar y combinar prompts
        system_prompt = self._load_combined_prompt('base_chart_analysis.md')
        
        # Crear agente para imágenes/charts
        self.chart_agent = Agent[None, ChartData](
            model=model,
            output_type=ChartData,
            system_prompt=system_prompt
        )
        
        # Crear agente para texto (si está habilitado)
        self.text_analysis_enabled = self.config.analysis.get('analyze_text_with_ai', False)
        if self.text_analysis_enabled:
            text_prompt = self._load_combined_prompt('base_text_analysis.md')
            self.text_agent = Agent[None, TextAnalysis](
                model=model,
                output_type=TextAnalysis,
                system_prompt=text_prompt
            )
            print(f"  → Análisis de texto con IA: HABILITADO")
        else:
            self.text_agent = None
            print(f"  → Análisis de texto con IA: deshabilitado (solo regex)")
        
        print(f"✓ Agente inicializado con {provider.upper()}: {model_name}")
    
    def _load_combined_prompt(self, base_file: str = 'base_chart_analysis.md') -> str:
        """
        Carga y combina el prompt base con el contexto de dominio específico.
        
        Args:
            base_file: Nombre del archivo de prompt base a cargar
        
        Estructura:
        1. Prompt base (instrucciones generales de análisis)
        2. Contexto de dominio (terminología, métricas específicas)
        """
        prompts_config = self.config.prompts
        prompts_dir = Path(prompts_config.get('prompts_dir', 'prompts'))
        
        # Cargar prompt base
        base_prompt_path = prompts_dir / base_file
        
        try:
            with open(base_prompt_path, 'r', encoding='utf-8') as f:
                base_prompt = f.read()
        except FileNotFoundError:
            print(f"  ⚠️  No se encontró {base_prompt_path}, usando prompt por defecto")
            base_prompt = prompts_config.get('chart_analysis', 
                'Analiza este gráfico en detalle. Extrae todos los valores numéricos, categorías y tendencias.')
        
        # Cargar contexto de dominio (opcional)
        domain = prompts_config.get('domain')
        domain_prompt = ""
        
        if domain:
            domain_file = prompts_config.get('domain_prompts', {}).get(domain)
            if domain_file:
                domain_path = prompts_dir / 'domains' / domain_file
                try:
                    with open(domain_path, 'r', encoding='utf-8') as f:
                        domain_prompt = f.read()
                    print(f"  → Usando contexto de dominio: {domain}")
                except FileNotFoundError:
                    print(f"  ⚠️  No se encontró contexto para dominio '{domain}'")
        
        # Combinar prompts
        if domain_prompt:
            combined = f"{base_prompt}\n\n{'='*80}\n\n{domain_prompt}"
        else:
            combined = base_prompt
        
        return combined
    
    def _create_anthropic_model(self, model_name: str) -> AnthropicModel:
        """Crea modelo de Anthropic con manejo de API key"""
        # Intentar obtener API key de diferentes fuentes
        api_key = (
            os.getenv('ANTHROPIC_API_KEY') or 
            self.config.analysis.get('anthropic_api_key') or
            None  # Para ejecución en claude.ai
        )
        
        if api_key:
            print(f"  → Usando Anthropic API key desde {'entorno' if os.getenv('ANTHROPIC_API_KEY') else 'config'}")
        else:
            print(f"  → Modo claude.ai (sin API key explícita)")
        
        return AnthropicModel(model_name, api_key=api_key)
    
    def _create_openai_model(self, model_name: str):
        """Crea modelo de OpenAI con manejo de API key"""
        # OpenAI requiere la API key como variable de entorno
        api_key = (
            os.getenv('OPENAI_API_KEY') or 
            self.config.analysis.get('openai_api_key')
        )

        if not api_key:
            raise ValueError(
                "Se requiere API key para OpenAI. Configura:\n"
                "  1. Variable de entorno: export OPENAI_API_KEY='tu-key'\n"
                "  2. O en config.json: 'openai_api_key': 'tu-key'"
            )

        # Si la key viene de config.json, establecerla como variable de entorno
        if not os.getenv('OPENAI_API_KEY'):
            os.environ['OPENAI_API_KEY'] = api_key
            print(f"  → Usando OpenAI API key desde config")
        else:
            print(f"  → Usando OpenAI API key desde entorno")

        return OpenAIChatModel(model_name)
    
    def analyze_image(self, image_path: str) -> ChartData:
        """Analiza una imagen (gráfico) usando el modelo configurado"""
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

        # Mensaje del usuario mejorado con instrucciones específicas
        user_message = """Analiza este gráfico siguiendo las instrucciones del sistema.

IMPORTANTE:
1. Extrae TODOS los valores numéricos visibles con precisión
2. Identifica TODAS las categorías y series
3. Proporciona insights específicos basados en los datos
4. Calcula métricas relevantes (promedios, totales, variaciones)
5. Usa la terminología y contexto del dominio si aplica

Devuelve la información en el formato JSON estructurado especificado."""

        # Analizar con el agente
        result = self.chart_agent.run_sync(
            user_message,
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

        # Extraer el resultado estructurado
        if isinstance(result, ChartData):
            return result
        elif hasattr(result, 'output') and isinstance(result.output, ChartData):
            return result.output
        elif hasattr(result, 'data') and isinstance(result.data, ChartData):
            return result.data
        else:
            # Si no es ChartData, intentar parsear el texto como última opción
            print(f"  ⚠️  Resultado no estructurado: {type(result)}")
            # Devolver un ChartData vacío o con error
            return ChartData(
                chart_type="unknown",
                title="Error: No se pudo analizar",
                description=str(result)[:200] if hasattr(result, '__str__') else "Error desconocido"
            )
        
    def analyze_all_images(self, images: List[ImageData]) -> List[ChartData]:
        """Analiza todas las imágenes extraídas"""
        results = []
        for img in images:
            try:
                print(f"Analizando {img.filename}...")
                chart_data = self.analyze_image(img.path)
                # Solo agregar si es un ChartData válido
                if isinstance(chart_data, ChartData) and chart_data.chart_type != "unknown":
                    results.append(chart_data)
                else:
                    print(f"  ⚠️  Análisis fallido para {img.filename}")
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
    
    def analyze_text_with_ai(self, text_data: List[TextData]) -> List[TextData]:
        """
        Analiza el texto extraído usando IA para obtener insights más profundos.
        Requiere que analyze_text_with_ai esté habilitado en config.
        """
        if not self.text_analysis_enabled or not self.text_agent:
            print("  ⚠️  Análisis de texto con IA no está habilitado")
            return text_data
        
        print(f"  → Analizando {len(text_data)} páginas de texto con IA...")
        
        for text in text_data:
            try:
                # Solo analizar si hay contenido sustancial
                if len(text.content.strip()) < 50:
                    continue
                
                result = self.text_agent.run_sync(
                    f"Analiza el siguiente texto y extrae métricas, entidades e insights clave:\n\n{text.content[:4000]}"
                )
                
                # Extraer el resultado estructurado
                if isinstance(result, TextAnalysis):
                    text.ai_analysis = result
                elif hasattr(result, 'output') and isinstance(result.output, TextAnalysis):
                    text.ai_analysis = result.output
                elif hasattr(result, 'data') and isinstance(result.data, TextAnalysis):
                    text.ai_analysis = result.data
                    
            except Exception as e:
                print(f"  ⚠️  Error analizando página {text.page_number}: {e}")
        
        analyzed_count = sum(1 for t in text_data if t.ai_analysis is not None)
        print(f"  ✓ {analyzed_count} páginas analizadas con IA")
        
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
