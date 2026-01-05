# Procesador de Documentos PDF/PPT

Sistema modular para extraer y analizar contenido de documentos PDF y PowerPoint usando IA (Claude/OpenAI) con filtrado inteligente de imágenes y prompts especializados por dominio.

## 🚀 Características

- ✅ Extracción de texto de PDF y PPTX
- ✅ Extracción de imágenes y gráficos
- ✅ **Filtrado inteligente de imágenes con OCR** (descarta decoraciones sin valor)
- ✅ Análisis de gráficos con IA usando Pydantic-AI (Claude o OpenAI)
- ✅ **Sistema de prompts modular** (base + contexto de dominio)
- ✅ **Contextos especializados** (AFP Chile, genérico empresarial, extensible)
- ✅ Identificación automática de métricas y porcentajes
- ✅ Configuración externalizada en JSON
- ✅ Código simple y agnóstico

## 📦 Instalación

```bash
pip install -r requirements.txt
```

### Requisito adicional: Tesseract OCR

Para el filtrado de imágenes, instala Tesseract:

**Windows:**
```powershell
# Con chocolatey
choco install tesseract

# O descargar desde: https://github.com/UB-Mannheim/tesseract/wiki
```

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

## 🔧 Configuración

### API Keys

**Opción 1 (Recomendada)** - Variables de entorno:
```bash
export ANTHROPIC_API_KEY='tu-key'
export OPENAI_API_KEY='tu-key'
```

**Opción 2** - En `config.json`:
```json
{
  "analysis": {
    "provider": "openai",
    "anthropic_api_key": "tu-key",
    "openai_api_key": "tu-key"
  }
}
```

### Seleccionar Dominio

Edita `config.json` para especificar el contexto empresarial:

```json
{
  "prompts": {
    "domain": "afp_chile"  // o "generic" para empresas generales
  }
}
```

Dominios disponibles:
- **`afp_chile`**: Administradoras de Fondos de Pensiones chilenas
- **`generic`**: Empresas y reportes corporativos generales
- **`null`**: Sin contexto específico (solo análisis base)

### Agregar Nuevo Dominio

1. Crea `prompts/domains/mi_empresa.md` con contexto especializado
2. Regístralo en `config.json`:
   ```json
   "domain_prompts": {
     "mi_empresa": "mi_empresa.md"
   }
   ```
3. Actívalo: `"domain": "mi_empresa"`

Ver [prompts/README.md](prompts/README.md) para más detalles.

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
├── image_filter.py      # Filtrado de imágenes con OCR
├── analyzer.py          # Análisis con IA
├── main.py              # Script principal
├── prompts/             # Sistema de prompts modular
│   ├── README.md        # Documentación de prompts
│   ├── base_chart_analysis.md    # Instrucciones base
│   └── domains/         # Contextos especializados
│       ├── afp_chile.md # Contexto AFP Chile
│       └── generic.md   # Contexto empresarial
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