# Procesador de Documentos PDF/PPT

Sistema modular para extraer y analizar contenido de documentos PDF y PowerPoint usando Pydantic y Claude AI.

## 🚀 Características

- ✅ Extracción de texto de PDF y PPTX
- ✅ Extracción de imágenes y gráficos
- ✅ Análisis de gráficos con Claude AI usando Pydantic-AI
- ✅ Identificación automática de métricas y porcentajes
- ✅ Configuración externalizada en JSON
- ✅ Código simple y agnóstico

## 📦 Instalación

```bash
pip install -r requirements.txt
```

## 🔧 Configuración

Edita `config.json` para personalizar:

- **Directorios de salida**: Dónde se guardan imágenes, texto y datos
- **Parámetros de análisis**: Modelo de Claude, temperatura, tokens
- **Prompts**: Instrucciones para el análisis de gráficos

## 📖 Uso

### Uso básico

```bash
python main.py documento.pdf
```

### Con configuración personalizada

```bash
python main.py documento.pptx --config mi_config.json
```

## 📁 Estructura de Archivos

```
.
├── config.json          # Configuración del sistema
├── models.py            # Modelos Pydantic
├── extractor.py         # Extracción de PDF/PPT
├── analyzer.py          # Análisis con Claude
├── main.py              # Script principal
├── requirements.txt     # Dependencias
└── output/              # Directorio de salida
    ├── images/          # Imágenes extraídas
    ├── text/            # Texto extraído
    └── data/            # Análisis JSON
```

## 🔍 Ejemplo de Salida

El sistema genera un archivo JSON con:

```json
{
  "filename": "documento.pdf",
  "total_pages": 50,
  "extraction_date": "2025-12-30T10:30:00",
  "text_data": [...],
  "image_data": [...],
  "chart_analysis": [
    {
      "chart_type": "bar",
      "title": "Evolución de Imagen",
      "categories": ["Habitat", "Cuprum", "Modelo"],
      "values": [26, 10, 23],
      "insights": ["Habitat lidera con 26%..."]
    }
  ]
}
```

## 🛠️ Uso Programático

```python
from extractor import DocumentExtractor
from analyzer import DocumentAnalyzer

# Extraer contenido
extractor = DocumentExtractor()
text_data, image_data = extractor.extract("documento.pdf")

# Analizar gráficos
analyzer = DocumentAnalyzer()
chart_analysis = analyzer.analyze_all_images(image_data)
```

## 📝 Notas

- El sistema requiere acceso a la API de Claude (configurado automáticamente en claude.ai)
- Los PDFs deben tener texto extraíble (no escaneos sin OCR)
- Las imágenes se analizan individualmente para maximizar precisión

## 🤝 Personalización

Puedes extender fácilmente:

1. **Nuevos formatos**: Agrega métodos en `DocumentExtractor`
2. **Análisis adicionales**: Extiende los modelos en `models.py`
3. **Prompts personalizados**: Modifica `config.json`

## 📊 Tipos de Gráficos Soportados

Claude puede analizar:
- Gráficos de barras
- Gráficos de líneas
- Gráficos circulares (pie)
- Tablas de datos
- Gráficos combinados
- Mapas de calor
- Y más...