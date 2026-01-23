import json
import os
from pathlib import Path
from typing import List
from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIChatModel
from models import ChartData, ChartResource, ChartAnalysisResult, ImageData, Config, TextData, TextAnalysis, DocumentMetadata


class DocumentAnalyzer:
    # Modelos válidos conocidos por proveedor
    VALID_MODELS = {
        'anthropic': ['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307',
                      'claude-3-5-sonnet-20241022', 'claude-3-5-sonnet-20240620'],
        'openai': ['gpt-4', 'gpt-4-turbo', 'gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo',
                   'gpt-4-vision-preview', 'gpt-4-turbo-preview']
    }
    
    def __init__(self, config_path: str = "config.json", domain_prompts_file: str = None):
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        self.config = Config(**config_data)
        self.domain_prompts_file = domain_prompts_file
        
        # Obtener configuración del proveedor
        provider = self.config.analysis.get('provider', 'anthropic').lower()
        model_name = self.config.analysis['model']
        
        # Advertir si el modelo no está en la lista conocida
        if provider in self.VALID_MODELS and model_name not in self.VALID_MODELS[provider]:
            print(f"  ⚠️  ADVERTENCIA: '{model_name}' no está en la lista de modelos conocidos de {provider.upper()}")
            print(f"  ⚠️  Modelos válidos: {', '.join(self.VALID_MODELS[provider])}")
            print(f"  ⚠️  El modelo puede funcionar si es interno/beta, pero verifica si hay errores.")
        
        # Crear modelo según el proveedor
        if provider == 'anthropic':
            model = self._create_anthropic_model(model_name)
        elif provider == 'openai':
            model = self._create_openai_model(model_name)
        else:
            raise ValueError(f"Proveedor no soportado: {provider}. Use 'anthropic' o 'openai'")
        
        # Cargar y combinar prompts
        system_prompt = self._load_combined_prompt('base_chart_analysis.md')
        
        # Crear agente para imágenes/charts (usa ChartAnalysisResult sin info de recurso)
        self.chart_agent = Agent[None, ChartAnalysisResult](
            model=model,
            output_type=ChartAnalysisResult,
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
        
        # Modo verbose para logging detallado
        self.verbose = self.config.analysis.get('verbose', True)
        
        # Crear agente para metadata (ligero, sin prompts de dominio)
        self.metadata_agent = Agent[None, DocumentMetadata](
            model=model,
            output_type=DocumentMetadata,
            system_prompt="""Extrae metadata del documento analizando EL NOMBRE DEL ARCHIVO, título, portada y primeras páginas.

CRÍTICO: El nombre del archivo suele contener información valiosa sobre año, empresa y nombre del estudio.

**Prioridad de fuentes:**
1. **Nombre del archivo**: Parsea año (YYYY o YY), nombres de empresas, palabras clave del estudio
2. **Portada/Título**: Busca información formal del documento
3. **Primeras páginas**: Metadata adicional en encabezados o pie de página

**Ejemplos de parseo del nombre de archivo:**
- "2024_informe_satisfaccion_afp_habitat.pdf" → year:2024, name:"Informe de Satisfacción", company:"AFP Habitat"
- "2025_Ipsos_estudio_whatsapp.pptx" → year:2025, company:"Ipsos", name:"Estudio WhatsApp"
- "2017_Steerco2Segmentacion_v_resumida3.pdf" → year:2017, name:"Segmentación Steerco"
- "informe_resultados_2023_habitat.pdf" → year:2023, company:"Habitat", name:"Informe de Resultados"

**Heurísticas de parseo:**
- Años: 4 dígitos (2020-2030) o 2 dígitos al inicio (17→2017, 25→2025)
- Empresas comunes: Ipsos, Habitat, AFP, Cadem, GfK, Nielsen, Adimark
- Guiones bajos (_) y guiones (-) separan componentes
- "V1", "v2", "resumida", "final" son versiones, NO parte del nombre

IMPORTANTE: Si no encuentras un dato con certeza, deja el campo en null. No inventes.

**Campos a extraer:**
- **study_year**: Año del estudio (YYYY)
- **study_name**: Título/nombre del estudio
- **company**: Empresa/consultora responsable
- **report_type**: Tipo (informe, presentación, análisis, etc.)"""
        )
        
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
        
        base_prompt_path = prompts_dir / base_file
        
        try:
            with open(base_prompt_path, 'r', encoding='utf-8') as f:
                base_prompt = f.read()
        except FileNotFoundError:
            print(f"  ⚠️  No se encontró {base_prompt_path}, usando prompt por defecto")
            base_prompt = prompts_config.get('chart_analysis', 
                'Analiza este gráfico en detalle. Extrae todos los valores numéricos, categorías y tendencias.')
        
        domain_prompt = ""
        
        if self.domain_prompts_file:
            domain_file = self.domain_prompts_file if self.domain_prompts_file.endswith('.md') else f"{self.domain_prompts_file}.md"
            domain_path = prompts_dir / 'domains' / domain_file
            try:
                with open(domain_path, 'r', encoding='utf-8') as f:
                    domain_prompt = f.read()
                print(f"  → Usando contexto de dominio: {self.domain_prompts_file}")
            except FileNotFoundError:
                print(f"  ⚠️  No se encontró {domain_path}")
        
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
    
    def analyze_image(self, image_data: ImageData) -> ChartData:
        """Analiza una imagen (gráfico/tabla) usando el modelo configurado"""
        image_path = image_data.path
        with open(image_path, 'rb') as f:
            image_bytes = f.read()

        ext = Path(image_path).suffix.lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        media_type = mime_types.get(ext, 'image/png')

        # Construir el prompt base
        user_prompt = """Analiza este gráfico/tabla siguiendo las instrucciones del sistema.

IMPORTANTE:
1. Extrae TODOS los valores numéricos visibles con precisión
2. Identifica TODAS las categorías y series
3. Proporciona insights específicos basados en los datos
4. Calcula métricas relevantes (promedios, totales, variaciones)
5. Usa la terminología y contexto del dominio si aplica"""

        # Si es un gráfico compuesto, agregar el contexto textual
        if image_data.is_composite and image_data.context_text:
            user_prompt += f"""

NOTA IMPORTANTE - GRÁFICO COMPUESTO:
Este gráfico tiene valores numéricos y etiquetas que están renderizados como texto 
separado de la imagen. A continuación se proporciona el texto extraído del PDF que 
está cerca o superpuesto al gráfico. UTILIZA ESTOS VALORES para complementar tu análisis:

--- TEXTO DEL PDF CERCA DEL GRÁFICO ---
{image_data.context_text}
--- FIN DEL TEXTO ---

Combina la información visual del gráfico con los valores numéricos del texto para 
proporcionar un análisis completo y preciso."""

            if self.verbose:
                print(f"  📊 Gráfico compuesto: agregando {len(image_data.context_text)} chars de contexto")

        user_prompt += "\n\nDevuelve la información en el formato JSON estructurado especificado."

        image_content = BinaryContent(data=image_bytes, media_type=media_type)
        
        if self.verbose:
            print(f"  → Enviando imagen ({len(image_bytes)} bytes, {media_type})")

        try:
            result = self.chart_agent.run_sync([user_prompt, image_content])
        except Exception as e:
            print(f"  ❌ Error al analizar imagen: {e}")
            raise

        analysis_result = None
        if isinstance(result, ChartAnalysisResult):
            analysis_result = result
        elif hasattr(result, 'output') and isinstance(result.output, ChartAnalysisResult):
            analysis_result = result.output
        elif hasattr(result, 'data') and isinstance(result.data, ChartAnalysisResult):
            analysis_result = result.data
        else:
            print(f"  ⚠️  Resultado no estructurado: {type(result)}")
            return ChartData(
                chart_data=ChartResource(
                    type="unknown",
                    resource=image_data.path,
                    resource_type="image"
                ),
                title="Error: No se pudo analizar",
                description=str(result)[:200] if hasattr(result, '__str__') else "Error desconocido"
            )
        
        # Convertir ChartAnalysisResult a ChartData agregando información del recurso
        return ChartData(
            chart_data=ChartResource(
                type=analysis_result.chart_type,
                resource=image_data.path,
                resource_type="image"
            ),
            title=analysis_result.title,
            description=analysis_result.description,
            categories=analysis_result.categories,
            series=analysis_result.series,
            values=analysis_result.values,
            insights=analysis_result.insights,
            metrics=analysis_result.metrics,
            relevance_score=analysis_result.relevance_score
        )
        
    def analyze_all_images(self, images: List[ImageData]) -> List[ChartData]:
        """Analiza todas las imágenes extraídas"""
        results = []
        for img in images:
            try:
                print(f"Analizando {img.filename}...")
                chart_data = self.analyze_image(img)
                # Solo agregar si es un ChartData válido
                if isinstance(chart_data, ChartData) and chart_data.chart_data.type != "unknown":
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
    
    def _parse_filename_metadata(self, filename: str) -> DocumentMetadata:
        """
        Extrae metadata del nombre del archivo usando regex.
        Este es el método principal y garantizado para extraer año, empresa y nombre.
        
        Ejemplos de nombres soportados:
        - 2024_informe_resultados_afp_habitat.pdf
        - 2025_Ipsos_estudio_nuevo_canal_whatsapp.pdf
        - Informe_Semestral_Sector_AFP_1°-2025.pdf
        - 2017_Steerco2Segmentacion_v_resumida3.pdf
        """
        import re
        
        # Limpiar extensión y obtener nombre base
        name_without_ext = Path(filename).stem
        
        # Normalizar separadores a espacios para facilitar parseo
        normalized = re.sub(r'[_\-]+', ' ', name_without_ext)
        
        # ===== EXTRAER AÑO =====
        study_year = None
        
        # Patrón 1: Año de 4 dígitos (2017-2030)
        year_match = re.search(r'\b(20[1-3]\d)\b', normalized)
        if year_match:
            study_year = int(year_match.group(1))
        else:
            # Patrón 2: Año de 2 dígitos al inicio (17, 24, 25 -> 2017, 2024, 2025)
            year_2digit = re.match(r'^(\d{2})\s', normalized)
            if year_2digit:
                year_val = int(year_2digit.group(1))
                if 15 <= year_val <= 30:
                    study_year = 2000 + year_val
            else:
                # Patrón 3: Año de 2 dígitos al final con mes (Ago25, Dic24, etc.)
                year_with_month = re.search(r'(?:Ene|Feb|Mar|Abr|May|Jun|Jul|Ago|Sep|Oct|Nov|Dic)\s*(\d{2})\b', normalized, re.IGNORECASE)
                if year_with_month:
                    year_val = int(year_with_month.group(1))
                    if 15 <= year_val <= 30:
                        study_year = 2000 + year_val
        
        # ===== EXTRAER EMPRESA =====
        company = None
        
        # Lista de empresas/consultoras conocidas (case-insensitive)
        known_companies = [
            ('ipsos', 'Ipsos'),
            ('cadem', 'Cadem'),
            ('gfk', 'GfK'),
            ('nielsen', 'Nielsen'),
            ('adimark', 'Adimark'),
            ('criteria', 'Criteria'),
            ('feedback', 'Feedback'),
            ('habitat', 'AFP Habitat'),
            ('afp habitat', 'AFP Habitat'),
            ('provida', 'AFP Provida'),
            ('cuprum', 'AFP Cuprum'),
            ('capital', 'AFP Capital'),
            ('modelo', 'AFP Modelo'),
            ('planvital', 'AFP PlanVital'),
            ('chilquinta', 'Chilquinta'),
            ('steerco', 'Steerco'),
            ('bbk', 'BBK'),
            ('ocular', 'Ocular'),
            ('prudential', 'Prudential'),
        ]
        
        normalized_lower = normalized.lower()
        for pattern, company_name in known_companies:
            if pattern in normalized_lower:
                company = company_name
                break
        
        # ===== EXTRAER NOMBRE DEL ESTUDIO =====
        study_name = None
        
        # Remover año, versiones y empresa del nombre
        name_cleaned = normalized
        
        # Remover año (4 dígitos)
        name_cleaned = re.sub(r'\b20[1-3]\d\b', '', name_cleaned)
        # Remover año (2 dígitos al inicio)
        name_cleaned = re.sub(r'^\d{2}\s+', '', name_cleaned)
        # Remover mes+año abreviado (Ago25, Dic24, etc.)
        name_cleaned = re.sub(r'\b(?:Ene|Feb|Mar|Abr|May|Jun|Jul|Ago|Sep|Oct|Nov|Dic)\s*\d{2}\b', '', name_cleaned, flags=re.IGNORECASE)
        # Remover indicadores de versión
        name_cleaned = re.sub(r'\b[vV]\d+\b', '', name_cleaned)
        name_cleaned = re.sub(r'\bpensionv\d+\b', 'pension', name_cleaned, flags=re.IGNORECASE)  # Caso especial
        name_cleaned = re.sub(r'\bresumida?\d*\b', '', name_cleaned, flags=re.IGNORECASE)
        name_cleaned = re.sub(r'\bfinal\d*\b', '', name_cleaned, flags=re.IGNORECASE)
        # Remover empresas conocidas
        for pattern, _ in known_companies:
            name_cleaned = re.sub(rf'\b{re.escape(pattern)}\b', '', name_cleaned, flags=re.IGNORECASE)
        # Remover "AFP" suelto y números sueltos al final
        name_cleaned = re.sub(r'\bafp\b', '', name_cleaned, flags=re.IGNORECASE)
        name_cleaned = re.sub(r'\s+\d+\s*$', '', name_cleaned)  # Remover números al final
        # Limpiar espacios múltiples
        name_cleaned = re.sub(r'\s+', ' ', name_cleaned).strip()
        
        # Capitalizar el nombre si hay algo útil
        if name_cleaned and len(name_cleaned) > 3:
            # Capitalizar primera letra de cada palabra significativa
            words = name_cleaned.split()
            # Filtrar palabras muy cortas o numéricas
            words = [w for w in words if len(w) > 1 and not w.isdigit()]
            if words:
                study_name = ' '.join(w.capitalize() for w in words)
        
        # ===== DETECTAR TIPO DE REPORTE =====
        report_type = None
        type_patterns = [
            (r'\binforme\b', 'Informe'),
            (r'\bestudio\b', 'Estudio'),
            (r'\bpresentaci[oó]n\b', 'Presentación'),
            (r'\bresumen\b', 'Resumen'),
            (r'\banalisis\b', 'Análisis'),
            (r'\bdiagn[oó]stico\b', 'Diagnóstico'),
            (r'\bresultados\b', 'Informe de Resultados'),
            (r'\bsemestral\b', 'Informe Semestral'),
        ]
        
        for pattern, type_name in type_patterns:
            if re.search(pattern, normalized_lower):
                report_type = type_name
                break
        
        if self.verbose:
            print(f"  📁 Metadata parseada del nombre del archivo:")
            print(f"     Año: {study_year or 'N/A'}")
            print(f"     Empresa: {company or 'N/A'}")
            print(f"     Nombre: {study_name or 'N/A'}")
            print(f"     Tipo: {report_type or 'N/A'}")
        
        return DocumentMetadata(
            study_year=study_year,
            study_name=study_name,
            company=company,
            report_type=report_type
        )
    
    def _extract_metadata_from_text(self, text_data: List[TextData]) -> DocumentMetadata:
        """
        Intenta extraer metadata adicional del contenido del documento.
        Complementa lo obtenido del nombre del archivo.
        """
        import re
        
        if not text_data:
            return DocumentMetadata()
        
        # Combinar primeras 3 páginas
        first_pages_text = "\n".join([td.content[:1500] for td in text_data[:3]])
        
        # Buscar año en el texto (si no se encontró en el nombre)
        study_year = None
        year_patterns = [
            r'(?:estudio|informe|reporte|encuesta)\s+(?:de\s+)?(\d{4})',
            r'(\d{4})\s*[-–]\s*\d{4}',  # Rangos como 2024-2025
            r'(?:año|period[oa])\s+(\d{4})',
            r'(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(?:de\s+)?(\d{4})',
        ]
        for pattern in year_patterns:
            match = re.search(pattern, first_pages_text, re.IGNORECASE)
            if match:
                year_val = int(match.group(1))
                if 2015 <= year_val <= 2030:
                    study_year = year_val
                    break
        
        # Buscar empresa en el texto
        company = None
        company_patterns = [
            r'(?:elaborado|realizado|preparado)\s+por\s+([A-Z][a-zA-Z\s]+?)(?:\.|,|\n)',
            r'(?:©|copyright)\s*\d{4}\s+([A-Z][a-zA-Z\s]+?)(?:\.|,|\n)',
            r'^([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s*[-–—]\s*(?:Estudio|Informe)',
        ]
        for pattern in company_patterns:
            match = re.search(pattern, first_pages_text, re.MULTILINE)
            if match:
                company = match.group(1).strip()
                break
        
        return DocumentMetadata(
            study_year=study_year,
            company=company
        )
    
    def extract_metadata(self, filename: str, text_data: List[TextData]) -> DocumentMetadata:
        """
        Extrae metadata del documento usando un enfoque híbrido:
        1. Parseo del nombre del archivo (principal, siempre funciona)
        2. Extracción del contenido del texto (complementario)
        3. Opcionalmente, refinamiento con IA
        
        Args:
            filename: Nombre del archivo
            text_data: Lista de páginas de texto extraídas
        
        Returns:
            DocumentMetadata con información del estudio
        """
        if self.verbose:
            print(f"  → Extrayendo metadata del documento...")
        
        # Paso 1: Parsear nombre del archivo (SIEMPRE funciona)
        filename_metadata = self._parse_filename_metadata(filename)
        
        # Paso 2: Extraer del contenido del texto (complementario)
        text_metadata = self._extract_metadata_from_text(text_data)
        
        # Paso 3: Merge - priorizar filename, complementar con text
        final_metadata = DocumentMetadata(
            study_year=filename_metadata.study_year or text_metadata.study_year,
            study_name=filename_metadata.study_name,
            company=filename_metadata.company or text_metadata.company,
            report_type=filename_metadata.report_type
        )
        
        # Paso 4 (opcional): Si faltan datos críticos, intentar con IA
        use_ai_fallback = self.config.analysis.get('metadata_ai_fallback', False)
        
        if use_ai_fallback and (not final_metadata.study_year or not final_metadata.study_name):
            if self.verbose:
                print(f"  🤖 Intentando extracción con IA (faltan datos)...")
            try:
                first_pages = text_data[:2] if len(text_data) >= 2 else text_data
                combined_text = "\n".join([td.content[:800] for td in first_pages])
                
                prompt_text = f"""NOMBRE DEL ARCHIVO: {filename}

Extrae el año del estudio y el nombre/título del estudio.
Solo responde si estás seguro, de lo contrario deja null.

Texto de las primeras páginas:
{combined_text[:2000]}"""
                
                result = self.metadata_agent.run_sync(prompt_text)
                ai_metadata = result.data
                
                # Solo usar IA para llenar campos faltantes
                if not final_metadata.study_year and ai_metadata.study_year:
                    final_metadata.study_year = ai_metadata.study_year
                if not final_metadata.study_name and ai_metadata.study_name:
                    final_metadata.study_name = ai_metadata.study_name
                if not final_metadata.company and ai_metadata.company:
                    final_metadata.company = ai_metadata.company
                    
            except Exception as e:
                if self.verbose:
                    print(f"  ⚠️  Error en extracción IA: {e}")
        
        if self.verbose:
            print(f"  ✓ Metadata final:")
            print(f"     Año: {final_metadata.study_year or 'N/A'}")
            print(f"     Nombre: {final_metadata.study_name or 'N/A'}")
            print(f"     Empresa: {final_metadata.company or 'N/A'}")
            print(f"     Tipo: {final_metadata.report_type or 'N/A'}")
        
        return final_metadata


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
