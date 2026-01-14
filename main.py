import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Literal, List, Dict, Any
from extractor import DocumentExtractor
from analyzer import DocumentAnalyzer
from models import DocumentAnalysis, InsightItem


# Umbral mínimo de relevancia para incluir en el resumen de insights
DEFAULT_RELEVANCE_THRESHOLD = 0.5
# Filtro de tipo de insight: "all", "findings", "hypotheses", "actionable"
DEFAULT_INSIGHT_FILTER = "actionable"


def format_insight_text(insight: InsightItem, show_classification: bool = True) -> str:
    """Formatea un insight para mostrar en el resumen Markdown"""
    if show_classification:
        icons = {"finding": "📊", "hypothesis": "💡", "methodological_note": "📝"}
        labels = {"finding": "Hallazgo", "hypothesis": "Hipótesis", "methodological_note": "Nota metodológica"}
        icon = icons.get(insight.classification, "💡")
        classification_label = labels.get(insight.classification, "Hipótesis")
        sample_info = f" (N={insight.sample_size})" if insight.sample_size else ""
        return f"{icon} **[{classification_label}]**{sample_info} {insight.text}"
    return insight.text


def filter_insights_by_type(insights: list, insight_filter: str) -> list:
    """Filtra insights según el tipo especificado
    
    Opciones:
    - 'all': Todos los insights (hallazgos + hipótesis + notas metodológicas)
    - 'findings': Solo hallazgos cuantitativos
    - 'hypotheses': Solo hipótesis exploratorias
    - 'methodological_notes': Solo notas metodológicas/descriptivas
    - 'actionable': Hallazgos + hipótesis (excluye notas metodológicas)
    """
    if insight_filter == "all":
        return insights
    elif insight_filter == "findings":
        return [i for i in insights if i.classification == "finding"]
    elif insight_filter == "hypotheses":
        return [i for i in insights if i.classification == "hypothesis"]
    elif insight_filter == "methodological_notes":
        return [i for i in insights if i.classification == "methodological_note"]
    elif insight_filter == "actionable":
        return [i for i in insights if i.classification in ("finding", "hypothesis")]
    return insights


def save_ndjson(analysis: DocumentAnalysis, output_file: Path, source_file: str) -> Path:
    """
    Guarda el análisis en formato NDJSON con registros meta/claim/summary.
    Un JSON por línea, sin markdown.
    """
    ndjson_file = output_file.with_suffix('.ndjson')
    
    # Recopilar todos los claims con IDs únicos
    claims = []
    claim_id = 1
    
    # Claims de gráficos/imágenes
    for chart in analysis.chart_analysis:
        for insight in chart.insights:
            claims.append({
                "type": "claim",
                "id": f"C{claim_id:03d}",
                "page_number": None,  # No tenemos página exacta para imágenes
                "source": "chart",
                "source_title": chart.title,
                "classification": insight.classification,
                "claim_text": insight.text,
                "evidence": {
                    "n": insight.sample_size,
                    "data_type": insight.evidence_type or "unknown",
                    "base_label": None
                },
                "theme_tags": insight.theme_tags,
                "ambiguity_flags": insight.ambiguity_flags,
                "classification_rationale": insight.classification_rationale,
                "relevance_score": chart.relevance_score
            })
            claim_id += 1
    
    # Claims del análisis de texto
    for td in analysis.text_data:
        if td.ai_analysis and td.ai_analysis.insights:
            for insight in td.ai_analysis.insights:
                claims.append({
                    "type": "claim",
                    "id": f"C{claim_id:03d}",
                    "page_number": td.page_number,
                    "source": "text",
                    "source_title": None,
                    "classification": insight.classification,
                    "claim_text": insight.text,
                    "evidence": {
                        "n": insight.sample_size,
                        "data_type": insight.evidence_type or "unknown",
                        "base_label": None
                    },
                    "theme_tags": insight.theme_tags,
                    "ambiguity_flags": insight.ambiguity_flags,
                    "classification_rationale": insight.classification_rationale,
                    "relevance_score": td.ai_analysis.relevance_score
                })
                claim_id += 1
    
    # Contar por clasificación
    counts = {
        "total_claims": len(claims),
        "findings": len([c for c in claims if c["classification"] == "finding"]),
        "hypotheses": len([c for c in claims if c["classification"] == "hypothesis"]),
        "methodological_notes": len([c for c in claims if c["classification"] == "methodological_note"])
    }
    
    # Identificar hipótesis prioritarias para validar
    top_hypotheses_to_validate = []
    for c in claims:
        if c["classification"] == "hypothesis" and not c["evidence"]["n"]:
            top_hypotheses_to_validate.append({
                "id": c["id"],
                "why": "Sin N especificado",
                "suggested_n": 100
            })
            if len(top_hypotheses_to_validate) >= 5:
                break
    
    # Registro meta
    meta_record = {
        "type": "meta",
        "study": {
            "study_name": analysis.filename,
            "source_file": source_file,
            "report_date": None,  # Se podría extraer del documento
            "method": None,
            "sample_total_n": None
        },
        "extraction": {
            "extraction_date": analysis.extraction_date.isoformat(),
            "total_pages": analysis.total_pages,
            "charts_analyzed": len(analysis.chart_analysis),
            "images_extracted": len(analysis.image_data)
        }
    }
    
    # Registro summary
    summary_record = {
        "type": "summary",
        "counts": counts,
        "top_hypotheses_to_validate": top_hypotheses_to_validate,
        "method_limitations": []
    }
    
    # Escribir NDJSON
    with open(ndjson_file, 'w', encoding='utf-8') as f:
        # Línea 1: meta
        f.write(json.dumps(meta_record, ensure_ascii=False) + '\n')
        
        # Líneas de claims
        for claim in claims:
            f.write(json.dumps(claim, ensure_ascii=False) + '\n')
        
        # Última línea: summary
        f.write(json.dumps(summary_record, ensure_ascii=False) + '\n')
    
    return ndjson_file


def create_insights_summary(
    analysis: DocumentAnalysis, 
    output_file: Path, 
    relevance_threshold: float = DEFAULT_RELEVANCE_THRESHOLD,
    insight_filter: str = DEFAULT_INSIGHT_FILTER,
    show_classification: bool = True
) -> Path:
    """
    Crea un resumen breve de insights en formato Markdown.
    Solo incluye insights con relevance_score >= threshold.
    Filtra por tipo de insight según insight_filter.
    Máximo 4 insights por gráfico y por página de texto analizado.
    """
    insights_file = output_file.parent / f"insights-{output_file.stem.replace('_analysis', '')}.md"
    
    content = f"# Insights - {analysis.filename}\n\n"
    content += f"**Fecha de análisis**: {analysis.extraction_date.strftime('%Y-%m-%d %H:%M')}\n\n"
    content += f"**Total páginas**: {analysis.total_pages} | **Gráficos analizados**: {len(analysis.chart_analysis)}\n\n"
    
    # Mostrar filtros aplicados
    filter_label = {
        "all": "Todos", 
        "findings": "Solo Hallazgos", 
        "hypotheses": "Solo Hipótesis",
        "methodological_notes": "Solo Notas metodológicas",
        "actionable": "Hallazgos + Hipótesis (sin notas metodológicas)"
    }
    content += f"**Filtro**: {filter_label.get(insight_filter, insight_filter)} | **Umbral relevancia**: {relevance_threshold}\n\n"
    content += "---\n\n"
    
    # Leyenda de clasificación
    if show_classification:
        content += "> 📊 **Hallazgo**: Respaldado por datos cuantitativos (N alto)  \n"
        content += "> 💡 **Hipótesis**: Exploratorio o cualitativo (requiere validación)  \n"
        content += "> 📝 **Nota metodológica**: Descripción metodológica/contextual\n\n"
    
    has_insights = False
    total_findings = 0
    total_hypotheses = 0
    
    # Insights de gráficos/imágenes (filtrados por relevancia)
    if analysis.chart_analysis:
        relevant_charts = [
            chart for chart in analysis.chart_analysis 
            if chart.insights and chart.relevance_score >= relevance_threshold
        ]
        
        # Filtrar charts que tengan insights del tipo deseado
        charts_with_filtered_insights = []
        for chart in relevant_charts:
            filtered = filter_insights_by_type(chart.insights, insight_filter)
            if filtered:
                charts_with_filtered_insights.append((chart, filtered))
        
        if charts_with_filtered_insights:
            has_insights = True
            content += "## Insights de Gráficos\n\n"
            
            for chart_idx, (chart, filtered_insights) in enumerate(charts_with_filtered_insights, 1):
                content += f"### {chart_idx}. {chart.title or 'Sin título'} ({chart.chart_data.type})\n\n"
                
                top_insights = filtered_insights[:4]
                for insight in top_insights:
                    content += f"- {format_insight_text(insight, show_classification)}\n"
                    if insight.classification == "finding":
                        total_findings += 1
                    elif insight.classification == "hypothesis":
                        total_hypotheses += 1
                    # observations no se cuentan en el resumen
                content += "\n"
    
    # Insights del análisis de texto con IA (filtrados por relevancia)
    text_pages_with_insights = [
        td for td in analysis.text_data 
        if td.ai_analysis and td.ai_analysis.insights and td.ai_analysis.relevance_score >= relevance_threshold
    ]
    
    # Filtrar páginas que tengan insights del tipo deseado
    pages_with_filtered_insights = []
    for td in text_pages_with_insights:
        filtered = filter_insights_by_type(td.ai_analysis.insights, insight_filter)
        if filtered:
            pages_with_filtered_insights.append((td, filtered))
    
    if pages_with_filtered_insights:
        has_insights = True
        content += "## Insights del Análisis de Texto\n\n"
        
        for text_data, filtered_insights in pages_with_filtered_insights:
            content += f"### Página {text_data.page_number}\n\n"
            
            top_insights = filtered_insights[:4]
            for insight in top_insights:
                content += f"- {format_insight_text(insight, show_classification)}\n"
                if insight.classification == "finding":
                    total_findings += 1
                elif insight.classification == "hypothesis":
                    total_hypotheses += 1
                # observations no se cuentan en el resumen
            content += "\n"
    
    # Resumen de clasificación
    if has_insights:
        content += "---\n\n"
        content += f"**Resumen**: {total_findings} hallazgos | {total_hypotheses} hipótesis\n"
    else:
        content += "_No se encontraron insights relevantes en el análisis._\n"
        content += f"\n_Umbral de relevancia: {relevance_threshold}_\n"
    
    with open(insights_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return insights_file


def process_document(file_path: str, config_path: str = "config.json", domain_prompts_file: str = None) -> DocumentAnalysis:
    """
    Procesa un documento completo:
    1. Extrae texto e imágenes
    2. Analiza gráficos con IA (Claude o OpenAI)
    3. Guarda resultados
    """
    print(f"\n{'='*60}")
    print(f"Procesando: {file_path}")
    print(f"{'='*60}\n")
    
    # Paso 1: Extracción
    print("📄 Extrayendo contenido...")
    extractor = DocumentExtractor(config_path)
    text_data, image_data = extractor.extract(file_path)
    print(f"   ✓ {len(text_data)} páginas de texto")
    print(f"   ✓ {len(image_data)} imágenes")
    
    # Paso 2: Análisis
    print("\n🔍 Analizando contenido...")
    analyzer = DocumentAnalyzer(config_path, domain_prompts_file=domain_prompts_file)
    
    # Extraer métricas del texto (regex básico)
    text_data = analyzer.extract_text_metrics(text_data)
    print(f"   ✓ Métricas extraídas del texto (regex)")
    
    # Análisis de texto con IA (si está habilitado)
    if analyzer.text_analysis_enabled:
        text_data = analyzer.analyze_text_with_ai(text_data)
    
    # Analizar imágenes
    chart_analysis = []
    if image_data:
        print(f"   → Analizando {len(image_data)} gráficos/tablas con IA...")
        chart_analysis = analyzer.analyze_all_images(image_data)
        print(f"   ✓ {len(chart_analysis)} visualizaciones analizadas")
    
    # Paso 3: Crear análisis completo
    analysis = DocumentAnalysis(
        filename=Path(file_path).name,
        total_pages=len(text_data),
        text_data=text_data,
        image_data=image_data,
        chart_analysis=chart_analysis
    )
    
    # Paso 4: Guardar resultados
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    output_dir = Path(config['extraction']['output_dir']) / config['extraction']['data_dir']
    output_file = output_dir / f"{Path(file_path).stem}_analysis.ndjson"
    
    # Guardar en formato NDJSON (meta/claim/summary)
    ndjson_file = save_ndjson(analysis, output_file, file_path)
    
    print(f"\n💾 Resultados guardados en: {ndjson_file}")
    
    # Crear resumen de insights (con filtros de relevancia y tipo)
    relevance_threshold = config.get('analysis', {}).get('relevance_threshold', DEFAULT_RELEVANCE_THRESHOLD)
    insight_filter = config.get('analysis', {}).get('insight_filter', DEFAULT_INSIGHT_FILTER)
    show_classification = config.get('analysis', {}).get('show_insight_classification', True)
    
    insights_file = create_insights_summary(
        analysis, 
        ndjson_file,  # Cambiado de output_file a ndjson_file
        relevance_threshold,
        insight_filter,
        show_classification
    )
    print(f"📄 Resumen de insights: {insights_file}")
    
    # Calcular estadísticas de relevancia y clasificación
    relevant_charts = [c for c in analysis.chart_analysis if c.relevance_score >= relevance_threshold]
    relevant_text_pages = [t for t in analysis.text_data if t.ai_analysis and t.ai_analysis.relevance_score >= relevance_threshold]
    
    # Contar hallazgos vs hipótesis vs notas metodológicas
    total_findings = 0
    total_hypotheses = 0
    total_methodological = 0
    for chart in analysis.chart_analysis:
        for insight in chart.insights:
            if insight.classification == "finding":
                total_findings += 1
            elif insight.classification == "hypothesis":
                total_hypotheses += 1
            else:
                total_methodological += 1
    for td in analysis.text_data:
        if td.ai_analysis:
            for insight in td.ai_analysis.insights:
                if insight.classification == "finding":
                    total_findings += 1
                elif insight.classification == "hypothesis":
                    total_hypotheses += 1
                else:
                    total_methodological += 1
    
    # Mostrar resumen
    print(f"\n{'='*60}")
    print("RESUMEN")
    print(f"{'='*60}")
    print(f"Total páginas: {analysis.total_pages}")
    print(f"Imágenes extraídas: {len(analysis.image_data)}")
    print(f"Gráficos analizados: {len(analysis.chart_analysis)} ({len(relevant_charts)} relevantes)")
    if analyzer.text_analysis_enabled:
        total_text_analyzed = len([t for t in analysis.text_data if t.ai_analysis])
        print(f"Páginas de texto analizadas: {total_text_analyzed} ({len(relevant_text_pages)} relevantes)")
    print(f"Umbral de relevancia: {relevance_threshold}")
    print(f"📊 Hallazgos: {total_findings} | 💡 Hipótesis: {total_hypotheses} | 📝 Notas: {total_methodological}")
    
    if analysis.chart_analysis:
        print(f"\nPrimeros insights encontrados:")
        for i, chart in enumerate(analysis.chart_analysis[:3], 1):
            print(f"\n  {i}. {chart.title or 'Sin título'}")
            print(f"     Tipo: {chart.chart_data.type}")
            if chart.insights:
                first_insight = chart.insights[0]
                labels = {"finding": "Hallazgo", "hypothesis": "Hipótesis", "methodological_note": "Nota"}
                classification = labels.get(first_insight.classification, "Hipótesis")
                print(f"     [{classification}]: {first_insight.text[:80]}...")
    
    return analysis


def main():
    parser = argparse.ArgumentParser(
        description="Procesa documentos PDF/PPT extrayendo texto, imágenes y analizando gráficos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Configuración de API Keys:
  Opción 1 (Recomendada) - Variables de entorno:
    export ANTHROPIC_API_KEY='tu-key-anthropic'
    export OPENAI_API_KEY='tu-key-openai'
  
  Opción 2 - Archivo config.json:
    {
      "analysis": {
        "provider": "anthropic",  // o "openai"
        "anthropic_api_key": "tu-key",
        "openai_api_key": "tu-key"
      }
    }

Ejemplos:
  # Uso básico (prompts genéricos)
  python main.py documento.pdf
  
  # Con prompts específicos de dominio
  python main.py documento.pdf --domain-prompts afp_chile
  
  # Con configuración personalizada
  python main.py documento.pdf --config config_custom.json --domain-prompts afp_chile
        """
    )
    parser.add_argument(
        "file",
        help="Ruta al archivo PDF o PPTX a procesar"
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Ruta al archivo de configuración (default: config.json)"
    )
    parser.add_argument(
        "--domain-prompts",
        dest="domain_prompts",
        help="Nombre del archivo de prompts específicos del dominio (ej: afp_chile). Se busca en prompts/domains/"
    )
    
    args = parser.parse_args()
    
    # Validar archivo
    if not Path(args.file).exists():
        print(f"❌ Error: El archivo '{args.file}' no existe")
        return
    
    # Validar configuración
    if not Path(args.config).exists():
        print(f"❌ Error: El archivo de configuración '{args.config}' no existe")
        return
    
    try:
        analysis = process_document(args.file, args.config, domain_prompts_file=args.domain_prompts)
        print(f"\n✅ Proceso completado exitosamente")
    except Exception as e:
        print(f"\n❌ Error durante el procesamiento: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
