"""
Sintetizador de Insights Multi-Estudios

Este módulo consolida insights de múltiples estudios, identificando:
- Conclusiones recurrentes/consistentes
- Contradicciones entre estudios
- Evolución temporal de métricas

Uso:
    python synthesizer.py output/data/*.ndjson
    python synthesizer.py output/data/*.ndjson --only-findings
    python synthesizer.py output/data/*.ndjson --themes satisfaccion,NPS
"""

import json
import argparse
import glob
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
from datetime import datetime
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIChatModel
import os


class ClaimReference(BaseModel):
    """Referencia a un claim de un estudio"""
    study_name: str
    study_year: Optional[int]
    claim_id: str
    claim_text: str
    page_number: Optional[int]
    sample_size: Optional[int]
    classification: str


class ConsolidatedInsight(BaseModel):
    """Insight consolidado de múltiples estudios"""
    theme: str = Field(description="Tema principal del insight")
    consolidated_text: str = Field(description="Texto consolidado del insight")
    consistency_level: str = Field(description="'high', 'medium', 'low' o 'contradiction'")
    consistency_explanation: Optional[str] = Field(None, description="Explicación de consistencia o contradicción")
    supporting_claims: List[Dict[str, Any]] = Field(default_factory=list, description="Claims que respaldan")
    variation_range: Optional[str] = Field(None, description="Rango de variación si aplica (ej: '65-72%')")


class SynthesisResult(BaseModel):
    """Resultado completo de la síntesis"""
    consolidated_insights: List[ConsolidatedInsight]
    total_studies: int
    year_range: str
    total_claims_analyzed: int


class StudySynthesizer:
    """Sintetizador de insights de múltiples estudios"""
    
    def __init__(self, config_path: str = "config.json"):
        """Inicializa el sintetizador con configuración"""
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        self.config = config_data
        
        # Configurar modelo
        provider = config_data.get('analysis', {}).get('provider', 'anthropic').lower()
        model_name = config_data.get('analysis', {}).get('model')
        
        if provider == 'anthropic':
            api_key = os.getenv('ANTHROPIC_API_KEY') or config_data.get('analysis', {}).get('anthropic_api_key')
            model = AnthropicModel(model_name, api_key=api_key)
        elif provider == 'openai':
            api_key = os.getenv('OPENAI_API_KEY') or config_data.get('analysis', {}).get('openai_api_key')
            
            if not api_key:
                raise ValueError(
                    "Se requiere API key para OpenAI. Configura:\n"
                    "  1. Variable de entorno: export OPENAI_API_KEY='tu-key'\n"
                    "  2. O en config.json: 'openai_api_key': 'tu-key'"
                )
            
            # Si la key viene de config, establecerla como variable de entorno
            if not os.getenv('OPENAI_API_KEY'):
                os.environ['OPENAI_API_KEY'] = api_key
                print(f"  → Usando OpenAI API key desde config")
            else:
                print(f"  → Usando OpenAI API key desde entorno")
            
            model = OpenAIChatModel(model_name)
        else:
            raise ValueError(f"Proveedor no soportado: {provider}")
        
        # Crear agente para síntesis
        self.synthesis_agent = Agent[None, SynthesisResult](
            model=model,
            output_type=SynthesisResult,
            system_prompt=self._get_synthesis_prompt()
        )
        
        print(f"✓ Sintetizador inicializado con {provider.upper()}: {model_name}")
    
    def _get_synthesis_prompt(self) -> str:
        """Genera el prompt para el agente de síntesis"""
        return """Eres un analista experto en consolidar hallazgos de múltiples estudios de investigación.

Tu tarea es identificar:
1. **Conclusiones recurrentes**: Insights que aparecen en múltiples estudios con valores similares
2. **Contradicciones**: Insights que se contradicen entre estudios
3. **Patrones consistentes**: Tendencias que se mantienen en el tiempo

## Criterios de Consistencia

**HIGH (Alta consistencia):**
- Misma conclusión en 3+ estudios
- Variación de valores < 10 puntos porcentuales
- Tendencia clara y sostenida

**MEDIUM (Consistencia media):**
- Misma conclusión en 2 estudios
- Variación de valores 10-20pp
- Tendencia similar pero con fluctuaciones

**LOW (Baja consistencia):**
- Solo 1 estudio reporta
- Variación >20pp entre estudios similares

**CONTRADICTION (Contradicción):**
- Estudios reportan conclusiones opuestas
- Diferencias >30pp en métricas similares
- Tendencias invertidas

## Detección de Contradicciones

Busca:
- Valores muy diferentes para la misma métrica (ej: NPS de 60 vs NPS de 20)
- Conclusiones opuestas (ej: "satisfacción alta" vs "satisfacción baja")
- Tendencias invertidas (ej: "creció" vs "decreció")

## Formato de Salida

Para cada insight consolidado:
- **theme**: Categoría temática (ej: "Satisfacción General", "NPS", "Canales")
- **consolidated_text**: Resumen que integra todos los hallazgos
- **consistency_level**: high/medium/low/contradiction
- **consistency_explanation**: Si es contradicción, explica las diferencias
- **supporting_claims**: Lista con referencia a cada claim (no modificar)
- **variation_range**: Si aplica, rango de valores (ej: "65-72%", "NPS 45-62")

## Ejemplo

Input: 3 claims sobre satisfacción (68%, 71%, 65%)
Output:
```json
{
  "theme": "Satisfacción General",
  "consolidated_text": "La satisfacción general se mantiene consistentemente entre 65-71% en todos los estudios analizados",
  "consistency_level": "high",
  "consistency_explanation": null,
  "variation_range": "65-71%"
}
```

Input: 2 claims contradictorios (NPS 60 vs NPS -18)
Output:
```json
{
  "theme": "Net Promoter Score (NPS)",
  "consolidated_text": "Contradicción importante: un estudio reporta NPS positivo (60) mientras otro reporta NPS negativo (-18)",
  "consistency_level": "contradiction",
  "consistency_explanation": "Diferencia de 78 puntos sugiere diferentes poblaciones, metodologías o períodos. Requiere revisión.",
  "variation_range": "-18 a 60"
}
```

IMPORTANTE: Consolidar solo insights que hablen del mismo concepto/métrica."""
    
    def load_ndjson_files(self, file_paths: List[str], 
                          only_findings: bool = False,
                          theme_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Carga claims de múltiples archivos NDJSON
        
        Args:
            file_paths: Lista de rutas a archivos .ndjson
            only_findings: Si True, solo cargar hallazgos (excluir hipótesis)
            theme_filter: Lista de temas a filtrar (opcional)
        
        Returns:
            Lista de claims con metadata del estudio
        """
        all_claims = []
        
        for file_path in file_paths:
            path = Path(file_path)
            if not path.exists():
                print(f"⚠️  Archivo no encontrado: {file_path}")
                continue
            
            print(f"📖 Cargando: {path.name}")
            
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Primera línea es metadata
            if not lines:
                continue
            
            meta = json.loads(lines[0])
            # Usar nombre del archivo si study_name es None o vacío
            study_name = meta.get('study', {}).get('study_name')
            if not study_name:
                # Remover '_analysis' del stem para mejor legibilidad
                study_name = path.stem.replace('_analysis', '')
            study_year = meta.get('study', {}).get('study_year')
            
            # Resto son claims
            for line in lines[1:]:
                try:
                    record = json.loads(line)
                    if record.get('type') == 'claim':
                        # Filtrar por clasificación si se solicita
                        if only_findings and record.get('classification') != 'finding':
                            continue
                        
                        # Filtrar por tema si se solicita
                        if theme_filter:
                            tags = record.get('theme_tags', [])
                            if not any(theme.lower() in [t.lower() for t in tags] for theme in theme_filter):
                                continue
                        
                        # Agregar metadata del estudio
                        record['_study_name'] = study_name
                        record['_study_year'] = study_year
                        all_claims.append(record)
                except json.JSONDecodeError:
                    continue
        
        return all_claims
    
    def group_claims_by_theme(self, claims: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Agrupa claims por tema usando theme_tags"""
        theme_groups = defaultdict(list)
        
        for claim in claims:
            tags = claim.get('theme_tags', [])
            if not tags:
                # Si no tiene tags, usar un tag genérico
                tags = ['otros']
            
            # Agregar el claim a cada uno de sus temas
            for tag in tags:
                theme_groups[tag.lower()].append(claim)
        
        return dict(theme_groups)
    
    def synthesize_theme_group(self, theme: str, claims: List[Dict[str, Any]]) -> Optional[ConsolidatedInsight]:
        """
        Sintetiza un grupo de claims del mismo tema usando LLM
        
        Args:
            theme: Nombre del tema
            claims: Lista de claims del tema
        
        Returns:
            ConsolidatedInsight o None si no se puede sintetizar
        """
        # Si solo hay 1 claim, no hay nada que consolidar
        if len(claims) < 2:
            return None
        
        # Preparar contexto para el LLM
        context = f"Tema: {theme}\n\n"
        context += f"Claims a consolidar ({len(claims)}):\n\n"
        
        claim_refs = []
        for i, claim in enumerate(claims, 1):
            context += f"[Claim {i}]\n"
            context += f"Estudio: {claim['_study_name']}\n"
            if claim.get('_study_year'):
                context += f"Año: {claim['_study_year']}\n"
            context += f"Texto: {claim['claim_text']}\n"
            if claim.get('evidence', {}).get('n'):
                context += f"N: {claim['evidence']['n']}\n"
            context += "\n"
            
            # Guardar referencia
            claim_refs.append({
                'study_name': claim['_study_name'],
                'study_year': claim.get('_study_year'),
                'claim_id': claim['id'],
                'claim_text': claim['claim_text'],
                'page_number': claim.get('page_number'),
                'sample_size': claim.get('evidence', {}).get('n'),
                'classification': claim['classification']
            })
        
        context += "\nConsolida estos claims identificando consistencias o contradicciones."
        
        try:
            result = self.synthesis_agent.run_sync(context)
            
            # Extraer el resultado (manejar diferentes estructuras de respuesta)
            synthesis_result = None
            if isinstance(result, SynthesisResult):
                synthesis_result = result
            elif hasattr(result, 'output') and isinstance(result.output, SynthesisResult):
                synthesis_result = result.output
            elif hasattr(result, 'data') and isinstance(result.data, SynthesisResult):
                synthesis_result = result.data
            else:
                print(f"  ⚠️  Resultado no estructurado para '{theme}': {type(result)}")
                return None
            
            # Tomar el primer insight consolidado (debería haber solo uno por tema)
            if synthesis_result.consolidated_insights:
                insight = synthesis_result.consolidated_insights[0]
                insight.supporting_claims = claim_refs
                return insight
            
            return None
            
        except Exception as e:
            print(f"  ⚠️  Error sintetizando tema '{theme}': {e}")
            return None
    
    def synthesize_studies(self, file_paths: List[str],
                          only_findings: bool = False,
                          theme_filter: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Sintetiza múltiples estudios
        
        Args:
            file_paths: Rutas a archivos NDJSON
            only_findings: Solo procesar hallazgos
            theme_filter: Filtrar por temas específicos
        
        Returns:
            Diccionario con resultados de síntesis
        """
        print(f"\n{'='*60}")
        print("SINTETIZADOR DE ESTUDIOS")
        print(f"{'='*60}\n")
        
        # Cargar claims
        print("📚 Cargando claims de estudios...")
        all_claims = self.load_ndjson_files(file_paths, only_findings, theme_filter)
        
        if not all_claims:
            print("❌ No se encontraron claims para procesar")
            return None
        
        print(f"   ✓ {len(all_claims)} claims cargados de {len(file_paths)} estudios\n")
        
        # Agrupar por tema
        print("🏷️  Agrupando claims por tema...")
        theme_groups = self.group_claims_by_theme(all_claims)
        print(f"   ✓ {len(theme_groups)} temas identificados\n")
        
        # Sintetizar cada grupo
        print("🔍 Sintetizando por tema con IA...\n")
        consolidated_insights = []
        
        for theme, claims in sorted(theme_groups.items(), key=lambda x: len(x[1]), reverse=True):
            if len(claims) < 2:
                print(f"   ⊘ {theme}: solo 1 claim (omitido)")
                continue
            
            print(f"   → {theme}: {len(claims)} claims de {len(set(c['_study_name'] for c in claims))} estudios")
            insight = self.synthesize_theme_group(theme, claims)
            
            if insight:
                consolidated_insights.append(insight)
                symbol = "⚠️" if insight.consistency_level == "contradiction" else "✓"
                print(f"     {symbol} Consolidado: {insight.consistency_level}")
        
        # Calcular estadísticas
        years = [c.get('_study_year') for c in all_claims if c.get('_study_year')]
        year_range = f"{min(years)}-{max(years)}" if years else "N/A"
        
        studies = list(set(c['_study_name'] for c in all_claims))
        
        result = {
            'consolidated_insights': consolidated_insights,
            'total_studies': len(studies),
            'study_names': studies,
            'year_range': year_range,
            'total_claims_analyzed': len(all_claims),
            'themes_analyzed': len(theme_groups)
        }
        
        print(f"\n{'='*60}")
        print("RESUMEN")
        print(f"{'='*60}")
        print(f"Estudios analizados: {len(studies)}")
        print(f"Período cubierto: {year_range}")
        print(f"Claims analizados: {len(all_claims)}")
        print(f"Insights consolidados: {len(consolidated_insights)}")
        
        contradictions = [i for i in consolidated_insights if i.consistency_level == 'contradiction']
        if contradictions:
            print(f"⚠️  Contradicciones detectadas: {len(contradictions)}")
        
        return result
    
    def save_synthesis(self, synthesis: Dict[str, Any], output_file: Path):
        """Guarda la síntesis en formato Markdown y JSON"""
        
        # Generar Markdown
        md_content = self._generate_markdown(synthesis)
        md_file = output_file.with_suffix('.md')
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"\n💾 Síntesis guardada: {md_file}")
        
        # Generar JSON
        json_file = output_file.with_suffix('.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            # Convertir ConsolidatedInsight a dict
            json_data = {
                **synthesis,
                'consolidated_insights': [
                    insight.model_dump() if hasattr(insight, 'model_dump') else insight
                    for insight in synthesis['consolidated_insights']
                ]
            }
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        print(f"💾 Datos JSON guardados: {json_file}")
    
    def _generate_markdown(self, synthesis: Dict[str, Any]) -> str:
        """Genera reporte Markdown de la síntesis"""
        
        content = "# Síntesis de Estudios\n\n"
        content += f"**Fecha de síntesis**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        content += f"**Estudios analizados**: {synthesis['total_studies']}  \n"
        content += f"**Período cubierto**: {synthesis['year_range']}  \n"
        content += f"**Claims analizados**: {synthesis['total_claims_analyzed']}  \n"
        content += f"**Insights consolidados**: {len(synthesis['consolidated_insights'])}\n\n"
        
        # Listar estudios
        content += "### Estudios incluidos\n\n"
        for study in synthesis['study_names']:
            content += f"- {study}\n"
        content += "\n---\n\n"
        
        # Agrupar por nivel de consistencia
        insights_by_level = defaultdict(list)
        for insight in synthesis['consolidated_insights']:
            insights_by_level[insight.consistency_level].append(insight)
        
        # Orden de prioridad
        for level, emoji, title in [
            ('contradiction', '⚠️', 'Contradicciones Detectadas'),
            ('high', '✅', 'Conclusiones Altamente Consistentes'),
            ('medium', '📊', 'Conclusiones con Consistencia Media'),
            ('low', '📌', 'Conclusiones de Baja Recurrencia')
        ]:
            insights = insights_by_level.get(level, [])
            if not insights:
                continue
            
            content += f"## {emoji} {title}\n\n"
            
            for idx, insight in enumerate(insights, 1):
                content += f"### {idx}. {insight.theme.title()}\n\n"
                content += f"{insight.consolidated_text}\n\n"
                
                if insight.consistency_explanation:
                    content += f"**Explicación**: {insight.consistency_explanation}\n\n"
                
                if insight.variation_range:
                    content += f"**Rango de variación**: {insight.variation_range}\n\n"
                
                # Tabla de evidencia
                content += "| Estudio | Año | Claim | N | Pág. |\n"
                content += "|---------|-----|-------|---|------|\n"
                
                for claim in insight.supporting_claims:
                    year = claim.get('study_year', 'N/A')
                    text_short = claim['claim_text'][:80] + "..." if len(claim['claim_text']) > 80 else claim['claim_text']
                    n = claim.get('sample_size', '-')
                    n_str = f"{n:,}" if isinstance(n, int) else str(n)
                    page = claim.get('page_number', '-')
                    page_str = f"p.{page}" if page else '-'
                    
                    content += f"| {claim['study_name']} | {year} | {text_short} | {n_str} | {page_str} |\n"
                
                content += "\n"
                
                # Indicador de consistencia
                consistency_labels = {
                    'high': '✅ Alta consistencia',
                    'medium': '📊 Consistencia media',
                    'low': '📌 Baja recurrencia',
                    'contradiction': '⚠️ **CONTRADICCIÓN**'
                }
                content += f"**Nivel de consistencia**: {consistency_labels[insight.consistency_level]}\n\n"
                content += "---\n\n"
        
        return content


def main():
    parser = argparse.ArgumentParser(
        description="Sintetiza insights de múltiples estudios identificando conclusiones recurrentes y contradicciones",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Sintetizar todos los análisis
  python synthesizer.py output/data/*.ndjson
  
  # Solo hallazgos (excluir hipótesis)
  python synthesizer.py output/data/*.ndjson --only-findings
  
  # Filtrar por temas específicos
  python synthesizer.py output/data/*.ndjson --themes satisfaccion,NPS,canales
  
  # Especificar archivo de salida con ruta completa
  python synthesizer.py output/data/*.ndjson --output output/synthesis_afp_2024
  
  # Solo archivos de 2024
  python synthesizer.py output/data/2024*.ndjson --output output/synthesis_2024
        """
    )
    
    parser.add_argument(
        'files',
        nargs='+',
        help='Archivos NDJSON a sintetizar (acepta wildcards: *.ndjson, 2024*.ndjson, etc.)'
    )
    parser.add_argument(
        '--config',
        default='config.json',
        help='Ruta al archivo de configuración (default: config.json)'
    )
    parser.add_argument(
        '--only-findings',
        action='store_true',
        help='Solo procesar hallazgos (excluir hipótesis y notas metodológicas)'
    )
    parser.add_argument(
        '--themes',
        help='Filtrar por temas específicos (separados por coma: satisfaccion,NPS)'
    )
    parser.add_argument(
        '--output',
        default='output/synthesis',
        help='Ruta completa para archivo de salida (default: output/synthesis). Ejemplo: output/synthesis_afp_2024'
    )
    
    args = parser.parse_args()
    
    # Validar que exista el archivo de config
    if not Path(args.config).exists():
        print(f"❌ Error: No se encontró el archivo de configuración '{args.config}'")
        return
    
    # Expandir wildcards en los archivos (igual que main.py)
    all_files = []
    for pattern in args.files:
        if '*' in pattern or '?' in pattern:
            # Es un wildcard, expandir
            expanded = glob.glob(pattern)
            if expanded:
                all_files.extend(expanded)
            else:
                print(f"⚠️  No se encontraron archivos que coincidan con: {pattern}")
        else:
            # Es un archivo específico
            all_files.append(pattern)
    
    if not all_files:
        print("❌ Error: No se encontraron archivos NDJSON para procesar")
        return
    
    # Parsear filtro de temas
    theme_filter = [t.strip() for t in args.themes.split(',')] if args.themes else None
    
    # Inicializar sintetizador
    synthesizer = StudySynthesizer(args.config)
    
    # Sintetizar
    result = synthesizer.synthesize_studies(
        all_files,
        only_findings=args.only_findings,
        theme_filter=theme_filter
    )
    
    if result:
        # Guardar resultados
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        synthesizer.save_synthesis(result, output_path)


if __name__ == "__main__":
    main()
