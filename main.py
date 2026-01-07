import json
import argparse
from pathlib import Path
from extractor import DocumentExtractor
from analyzer import DocumentAnalyzer
from models import DocumentAnalysis


def create_insights_summary(analysis: DocumentAnalysis, output_file: Path) -> Path:
    """
    Crea un resumen breve de insights en formato Markdown.
    Máximo 4 insights por gráfico analizado.
    """
    insights_file = output_file.parent / f"insights-{output_file.stem.replace('_analysis', '')}.md"
    
    content = f"# Insights - {analysis.filename}\n\n"
    content += f"**Fecha de análisis**: {analysis.extraction_date.strftime('%Y-%m-%d %H:%M')}\n\n"
    content += f"**Total páginas**: {analysis.total_pages} | **Gráficos analizados**: {len(analysis.chart_analysis)}\n\n"
    content += "---\n\n"
    
    has_insights = False
    
    for chart_idx, chart in enumerate(analysis.chart_analysis, 1):
        if chart.insights:
            has_insights = True
            content += f"## {chart_idx}. {chart.title or 'Sin título'} ({chart.chart_data.type})\n\n"
            
            # Máximo 4 insights por gráfico
            top_chart_insights = chart.insights[:4]
            for insight in top_chart_insights:
                content += f"- {insight}\n"
            content += "\n"
    
    if not has_insights:
        content += "_No se encontraron insights en el análisis._\n"
    
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
    output_file = output_dir / f"{Path(file_path).stem}_analysis.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(analysis.model_dump_json(indent=2, exclude_none=True))
    
    print(f"\n💾 Resultados guardados en: {output_file}")
    
    # Crear resumen de insights
    insights_file = create_insights_summary(analysis, output_file)
    print(f"📄 Resumen de insights: {insights_file}")
    
    # Mostrar resumen
    print(f"\n{'='*60}")
    print("RESUMEN")
    print(f"{'='*60}")
    print(f"Total páginas: {analysis.total_pages}")
    print(f"Imágenes extraídas: {len(analysis.image_data)}")
    print(f"Gráficos analizados: {len(analysis.chart_analysis)}")
    
    if analysis.chart_analysis:
        print(f"\nPrimeros insights encontrados:")
        for i, chart in enumerate(analysis.chart_analysis[:3], 1):
            print(f"\n  {i}. {chart.title or 'Sin título'}")
            print(f"     Tipo: {chart.chart_data.type}")
            if chart.insights:
                print(f"     Insights: {chart.insights[0][:100]}...")
    
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
