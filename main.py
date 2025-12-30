import json
import argparse
from pathlib import Path
from extractor import DocumentExtractor
from analyzer import DocumentAnalyzer
from models import DocumentAnalysis


def process_document(file_path: str, config_path: str = "config.json") -> DocumentAnalysis:
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
    analyzer = DocumentAnalyzer(config_path)
    
    # Extraer métricas del texto
    text_data = analyzer.extract_text_metrics(text_data)
    print(f"   ✓ Métricas extraídas del texto")
    
    # Analizar imágenes
    chart_analysis = []
    if image_data:
        print(f"   → Analizando {len(image_data)} gráficos con IA...")
        chart_analysis = analyzer.analyze_all_images(image_data)
        print(f"   ✓ {len(chart_analysis)} gráficos analizados")
    
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
            print(f"     Tipo: {chart.chart_type}")
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
  # Usar con Claude (Anthropic)
  python main.py documento.pdf
  
  # Cambiar a OpenAI (modifica config.json primero)
  python main.py documento.pdf --config config_openai.json
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
        analysis = process_document(args.file, args.config)
        print(f"\n✅ Proceso completado exitosamente")
    except Exception as e:
        print(f"\n❌ Error durante el procesamiento: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
