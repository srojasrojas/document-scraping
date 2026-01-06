# Procesador de Documentos PDF/PPT

Sistema modular para extraer y analizar contenido de documentos PDF y PowerPoint usando IA (Claude/OpenAI) con filtrado inteligente de imágenes y prompts especializados por dominio.

## 🚀 Características

- ✅ Extracción de texto de PDF y PPTX
- ✅ Extracción de imágenes y gráficos
- ✅ **Filtrado inteligente de imágenes con OCR** (descarta decoraciones sin valor)
- ✅ Análisis de gráficos con IA usando Pydantic-AI (Claude o OpenAI)
- ✅ **Sistema de prompts modular** (base + contexto de dominio vía CLI)
- ✅ **Configuración genérica y reutilizable** entre empresas
- ✅ **Contextos especializados opcionales** (AFP Chile, sector financiero, etc.)
- ✅ Identificación automática de métricas y porcentajes
- ✅ Configuración externalizada en JSON
- ✅ Código simple y mantenible

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

### 1. API Keys

El sistema busca las API keys en este orden de prioridad:

**Opción 1 (Recomendada)** - Variables de entorno:

```powershell
# Windows PowerShell - Temporal (sesión actual)
$env:OPENAI_API_KEY = "sk-..."
$env:ANTHROPIC_API_KEY = "sk-ant-..."

# Windows PowerShell - Permanente
[System.Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'sk-...', 'User')
[System.Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY', 'sk-ant-...', 'User')
```

```bash
# Linux/Mac - Temporal
export OPENAI_API_KEY='sk-...'
export ANTHROPIC_API_KEY='sk-ant-...'

# Linux/Mac - Permanente (agregar a ~/.bashrc o ~/.zshrc)
echo 'export OPENAI_API_KEY="sk-..."' >> ~/.bashrc
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.bashrc
```

**Opción 2** - En `config.json` (no recomendado para repositorios compartidos):

```json
{
  "analysis": {
    "provider": "openai",
    "openai_api_key": "sk-...",
    "anthropic_api_key": "sk-ant-..."
  }
}
```

⚠️ **Importante**: Si usas `config.json` para las keys, no subas el archivo a Git. Usa `private_config.json` y agrégalo al `.gitignore`.

### 2. Seleccionar Proveedor y Modelo

Edita `config.json`:

```json
{
  "analysis": {
    "provider": "openai",     // o "anthropic"
    "model": "gpt-4o",        // o "claude-3-5-sonnet-20241022"
    "analyze_text_with_ai": false
  }
}
```

**Modelos soportados:**

**OpenAI:**
- `gpt-4o` (recomendado para visión)
- `gpt-4o-mini` (más económico)
- `gpt-4-turbo`
- `o1-preview`, `o1-mini` (razonamiento avanzado)

**Anthropic:**
- `claude-3-5-sonnet-20241022` (recomendado)
- `claude-3-5-haiku-20241022` (más rápido)
- `claude-3-opus-20240229` (máxima calidad)

### 3. Configuración del Filtro de Imágenes

El sistema usa OCR para determinar si una imagen contiene información valiosa:

```json
{
  "extraction": {
    "image_filter": {
      "enabled": true,
      "min_chars": 15,          // Mínimo caracteres para considerar valiosa
      "min_digits": 3,          // Mínimo números requeridos
      "min_words": 5,           // Mínimo palabras útiles
      "require_numbers": false, // Si true, rechaza imágenes sin números
      "ignore_words": [         // Palabras que no cuentan como "útiles"
        "logo", "www", "com", "http", "https",
        "copyright", "derechos", "reservados"
      ]
    }
  }
}
```

**Para casos específicos**, puedes agregar palabras a `ignore_words`:
- Nombres de empresas comunes en tus documentos
- Eslóganes repetitivos
- Términos legales estándar

## 📖 Uso

### Ejemplos Básicos

```bash
# Análisis genérico (sin contexto de dominio)
python main.py documento.pdf

# Con prompts específicos del sector AFP chileno
python main.py informe_afp.pdf --domain-prompts afp_chile

# Con configuración personalizada
python main.py documento.pptx --config mi_config.json

# Combinando opciones
python main.py reporte.pdf --config custom.json --domain-prompts finanzas
```

### Argumentos Disponibles

```
python main.py <archivo> [opciones]

Argumentos posicionales:
  archivo                  Ruta al PDF o PPTX a procesar

Opciones:
  --config PATH            Ruta al archivo de configuración
                          (default: config.json)
  
  --domain-prompts NOMBRE  Nombre del archivo de prompts de dominio
                          Se busca en prompts/domains/
                          Ejemplo: afp_chile (busca afp_chile.md)
```

### Crear Contexto de Dominio Personalizado

1. **Crea un archivo `.md` en `prompts/domains/`:**

```bash
# Ejemplo: prompts/domains/retail.md
```

2. **Define el contexto específico:**

```markdown
# CONTEXTO: Sector Retail

## Métricas Clave
- Ventas mismo local (SSS)
- Ticket promedio
- Unidades por transacción (UPT)
- Conversión
- Margen bruto

## Terminología
- POS: Point of Sale
- SKU: Stock Keeping Unit
- Shrinkage: Merma/pérdida de inventario
...
```

3. **Úsalo:**

```bash
python main.py reporte_retail.pdf --domain-prompts retail
```

**No necesitas modificar `config.json`** - el sistema busca automáticamente el archivo en `prompts/domains/`.

### Estructura de Prompts

El sistema combina dos niveles de prompts:

```
Prompt Final = Prompt Base + Prompt de Dominio (opcional)
```

- **Prompt Base** (`prompts/base_chart_analysis.md`): Instrucciones generales de análisis
- **Prompt de Dominio** (`prompts/domains/*.md`): Contexto especializado del sector

Ver [prompts/README.md](prompts/README.md) para guías detalladas.

## 📁 Estructura de Archivos

```
.
├── config.json                    # Configuración genérica del sistema
├── private_config.json            # (opcional) Config con API keys - no versionar
├── models.py                      # Modelos Pydantic
├── extractor.py                   # Extracción de PDF/PPT
├── image_filter.py                # Filtrado de imágenes con OCR
├── analyzer.py                    # Análisis con IA
├── main.py                        # Script principal
├── prompts/                       # Sistema de prompts modular
│   ├── README.md                  # Guía de prompts
│   ├── base_chart_analysis.md     # Instrucciones base (genérico)
│   ├── base_text_analysis.md      # Análisis de texto (opcional)
│   └── domains/                   # Contextos especializados
│       ├── afp_chile.md           # Sector AFP Chile
│       └── [tu_dominio].md        # Tus contextos personalizados
├── requirements.txt               # Dependencias Python
└── output/                        # Directorio de salida
    ├── images/                    # Imágenes extraídas y filtradas
    ├── text/                      # Texto extraído por página
    └── data/                      # Análisis JSON estructurado
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
extractor = DocumentExtractor("config.json")
text_data, image_data = extractor.extract("documento.pdf")

# Analizar gráficos (sin dominio específico)
analyzer = DocumentAnalyzer("config.json")
chart_analysis = analyzer.analyze_all_images(image_data)

# Analizar con dominio específico
analyzer = DocumentAnalyzer("config.json", domain_prompts_file="afp_chile")
chart_analysis = analyzer.analyze_all_images(image_data)

# Acceder a resultados
for chart in chart_analysis:
    print(f"Tipo: {chart.chart_type}")
    print(f"Título: {chart.title}")
    print(f"Insights: {chart.insights}")
```

## 🔧 Extender la Configuración

### Agregar Nuevos Parámetros

El archivo `config.json` es completamente extensible. Ejemplo:

```json
{
  "extraction": {
    "output_dir": "output",
    "image_dpi": 200,
    "custom_param": "valor"  // ← Tu parámetro personalizado
  },
  "analysis": {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.3,      // ← Control de creatividad
    "max_tokens": 4000,      // ← Límite de respuesta
    "verbose": true          // ← Logging detallado
  },
  "tu_seccion": {            // ← Nueva sección completa
    "opcion1": true,
    "opcion2": "valor"
  }
}
```

Luego accede en tu código:

```python
from models import Config

config = Config(**json.load(open("config.json")))
custom = config.extraction.get("custom_param")  # "valor"
```

### Crear Configuraciones por Ambiente

```bash
# Desarrollo
python main.py doc.pdf --config config_dev.json

# Producción
python main.py doc.pdf --config config_prod.json

# Testing
python main.py doc.pdf --config config_test.json
```

Cada archivo puede tener:
- Diferentes proveedores (OpenAI vs Anthropic)
- Diferentes umbrales de filtrado
- Diferentes directorios de salida
- API keys de diferentes cuentas

## 📝 Notas Técnicas

### Sistema de Análisis de Imágenes

- Las imágenes se pasan a los modelos usando `BinaryContent` de pydantic-ai
- Soporta múltiples proveedores (OpenAI, Anthropic) con el mismo código
- El filtro OCR descarta imágenes decorativas (logos, encabezados)
- Solo se analizan imágenes con contenido informativo (gráficos, tablas)

### Modelos de IA

- **OpenAI**: Requiere `OPENAI_API_KEY` como variable de entorno o en config
- **Anthropic**: Puede funcionar con API key o en modo claude.ai (sin key)
- El código verifica que el modelo exista antes de usarlo
- Advertencia si usas modelos beta o no documentados

### Requisitos de Documentos

- Los PDFs deben tener texto extraíble (no escaneos sin OCR previo)
- Las imágenes deben tener mínimo 100x100 píxeles
- Formatos soportados: PDF, PPT, PPTX
- Imágenes soportadas: PNG, JPG, JPEG, GIF, WEBP

## 🤝 Personalización y Extensión

### 1. Agregar Nuevos Formatos de Documento

Extiende `DocumentExtractor` en `extractor.py`:

```python
def extract_docx(self, file_path: str):
    """Extrae contenido de archivos .docx"""
    # Tu implementación
    pass
```

### 2. Personalizar Análisis

Modifica los modelos en `models.py` para capturar más información:

```python
class ChartData(BaseModel):
    chart_type: str
    title: str
    custom_metric: float  # ← Tu campo personalizado
    insights: List[str]
```

### 3. Agregar Nuevos Filtros de Imagen

Extiende `ImageFilter` en `image_filter.py`:

```python
def custom_filter(self, image_path: str) -> bool:
    """Tu lógica de filtrado personalizada"""
    # Ejemplo: detectar logos por colores
    # Ejemplo: clasificar por ML
    pass
```

### 4. Integrar con Otros Proveedores de IA

El sistema usa `pydantic-ai`, que soporta:
- OpenAI
- Anthropic
- Google Gemini
- Mistral
- Groq
- Ollama (local)

Para agregar uno nuevo, solo modifica `_create_model` en `analyzer.py`.

### 5. Crear Pipeline de Procesamiento

```python
# pipeline.py
import json
from pathlib import Path
from main import process_document

# Procesar todos los PDFs de un directorio
docs_dir = Path("documentos/")
for pdf in docs_dir.glob("*.pdf"):
    print(f"Procesando {pdf.name}")
    analysis = process_document(
        str(pdf),
        config_path="config.json",
        domain_prompts_file="afp_chile"
    )
    # Hacer algo con el análisis
    # Por ejemplo: guardar en base de datos, enviar email, etc.
```

## 📊 Tipos de Gráficos Soportados

Claude puede analizar:
- Gráficos de barras
- Gráficos de líneas
- Gráficos circulares (pie)
- Tablas de datos
- Gráficos combinados
- Mapas de calor
- Y más...