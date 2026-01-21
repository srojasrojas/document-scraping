# Procesador de Documentos PDF/PPT

Sistema modular para extraer y analizar contenido de documentos PDF y PowerPoint usando IA (Claude/OpenAI) con filtrado inteligente de imágenes y prompts especializados por dominio.

## 🚀 Características

- ✅ Extracción de texto de PDF y PPTX
- ✅ Extracción de imágenes y gráficos
- ✅ **Filtrado inteligente de imágenes con OCR** (descarta decoraciones sin valor)
- ✅ **Sistema de relevancia** (0-1) para filtrar contenido sin valor analítico
- ✅ **Detección de gráficos compuestos** (imagen + texto renderizado separado)
- ✅ Análisis de gráficos con IA usando Pydantic-AI (Claude o OpenAI)
- ✅ **Clasificación de insights**: Hallazgos (cuantitativos) vs Hipótesis (cualitativos) vs Observaciones (metodológicas)
- ✅ **Sistema de prompts modular** (base + contexto de dominio vía CLI)
- ✅ **Configuración genérica y reutilizable** entre empresas
- ✅ **Contextos especializados opcionales** (AFP Chile, sector financiero, etc.)
- ✅ **Resúmenes Markdown filtrados** por relevancia y tipo de insight
- ✅ Identificación automática de métricas y porcentajes
- ✅ Configuración externalizada en JSON
- ✅ Código simple y mantenible

## 📦 Instalación

```bash
pip install -r requirements.txt
```

### Requisitos adicionales

#### 1. Tesseract OCR (Obligatorio)

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

#### 2. LibreOffice (Para procesar PPTX)

Si necesitas procesar archivos PowerPoint (.pptx), instala LibreOffice:

**Windows:**
```powershell
# Con chocolatey (recomendado)
choco install libreoffice

# O descargar desde: https://www.libreoffice.org/download/download/
```

**macOS:**
```bash
brew install --cask libreoffice
```

**Linux:**
```bash
sudo apt-get install libreoffice
```

**Alternativa en Windows:** Si tienes Microsoft PowerPoint instalado, el sistema lo usará automáticamente (mayor calidad).

**Verificar instalación:**
```bash
# Debería mostrar la versión instalada
soffice --version
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
    "provider": "openai",              // o "anthropic"
    "model": "gpt-4o",                 // o "claude-3-5-sonnet-20241022"
    "analyze_text_with_ai": false,     // Analizar páginas de texto (lento)
    "relevance_threshold": 0.5,        // Umbral para insights (0-1)
    "insight_filter": "actionable",    // Tipo de insights a mostrar
    "show_insight_classification": true // Mostrar iconos de clasificación
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

### 4. Detección de Gráficos Compuestos

Algunos PDFs renderizan gráficos donde las barras/líneas son imágenes pero los valores numéricos están como texto separado. El sistema detecta automáticamente estos casos y enriquece el análisis:

```json
{
  "extraction": {
    "composite_detection": {
      "enabled": true,
      "proximity_margin": 50,      // Margen en puntos para buscar texto cercano
      "min_chart_width": 200,      // Ancho mínimo para considerar como gráfico
      "min_chart_height": 150,     // Alto mínimo para considerar como gráfico
      "min_page_ratio": 0.1,       // Ratio mínimo respecto a la página
      "min_nearby_numbers": 3,     // Mínimo números en texto cercano
      "ocr_number_threshold": 2,   // Si OCR detecta menos números, es candidato
      "verbose": true
    }
  }
}
```

**¿Cómo funciona?**
1. Extrae las posiciones (bounding boxes) de las imágenes en el PDF
2. Extrae el texto con coordenadas de cada página
3. Identifica texto que está superpuesto o cercano a cada imagen
4. Si la imagen parece un gráfico (por dimensiones) y hay números en el texto cercano, 
   pero el OCR de la imagen detectó pocos números → es un gráfico compuesto
5. Al analizar con IA, se incluye el texto extraído como contexto adicional

### 5. Conversión Automática de PowerPoint (PPTX → PDF)

El sistema convierte automáticamente archivos PPTX a PDF antes del análisis, aprovechando todo el pipeline existente (incluyendo detección de gráficos compuestos):

```json
{
  "extraction": {
    "pptx_conversion": {
      "enabled": true,
      "backend": "auto",          // "auto", "libreoffice", o "powerpoint"
      "dpi": 300,                 // Resolución de conversión (mayor = mejor calidad)
      "delete_temp_pdf": false,   // Si eliminar PDF temporal después del análisis
      "temp_dir": "output/temp_pdfs"  // Directorio para PDFs temporales
    }
  }
}
```

**Backends disponibles:**

| Backend | Requisito | Calidad | Plataforma |
|---------|-----------|---------|------------|
| `libreoffice` | LibreOffice instalado | Muy buena | Windows/Mac/Linux |
| `powerpoint` | Microsoft PowerPoint | Excelente | Solo Windows |
| `auto` | Detecta automáticamente | - | Todas (preferencia: PowerPoint → LibreOffice) |

**¿Cómo funciona?**
1. Detecta archivos `.pptx` al procesar
2. Convierte a PDF usando el backend disponible
3. Guarda el PDF en `temp_dir` (default: `output/temp_pdfs/`)
4. Procesa el PDF normalmente con todo el pipeline
5. Opcionalmente elimina el PDF temporal si `delete_temp_pdf: true`

**Ventajas:**
- ✅ Aprovecha toda la infraestructura de análisis de PDFs
- ✅ Detecta gráficos compuestos en presentaciones
- ✅ Mantiene alta calidad de conversión (DPI configurable)
- ✅ Funciona automáticamente sin intervención manual

**Nota:** Se recomienda `delete_temp_pdf: false` para debugging. Si algo falla, puedes revisar el PDF generado.

### 6. Clasificación de Insights y Filtrado

El sistema clasifica cada insight en tres categorías según su valor analítico:

| Clasificación | Icono | Descripción | Ejemplo |
|---------------|-------|-------------|---------|
| **Finding** (Hallazgo) | 📊 | Respaldado por datos cuantitativos con N ≥ 100 | "N=1260 casos con satisfacción de 68%" |
| **Hypothesis** (Hipótesis) | 💡 | Observación cualitativa que requiere validación | "Los usuarios reportan confusión con el proceso" |
| **Observation** (Observación) | 📝 | Descripción metodológica/contextual sin valor analítico | "El estudio utiliza encuestas telefónicas" |

**Configuración del filtro:**

```json
{
  "analysis": {
    "relevance_threshold": 0.5,        // Solo insights con score ≥ 0.5
    "insight_filter": "actionable",    // Tipo de insights a incluir
    "show_insight_classification": true // Mostrar iconos y etiquetas
  }
}
```

**Opciones de `insight_filter`:**

| Valor | Qué muestra en el resumen Markdown |
|-------|-----------------------------------|
| `"all"` | Todos (hallazgos + hipótesis + observaciones) |
| `"findings"` | Solo hallazgos cuantitativos |
| `"hypotheses"` | Solo hipótesis exploratorias |
| `"observations"` | Solo observaciones metodológicas |
| **`"actionable"`** | **Hallazgos + hipótesis (excluye observaciones) ← Recomendado** |

**¿Por qué usar `"actionable"`?**  
Las observaciones metodológicas ("El estudio abarca 2015-2025", "La muestra incluye mayores de 18 años") tienen valor documental pero NO son insights accionables. El filtro `actionable` las excluye del resumen manteniendo solo conclusiones útiles.

**Cómo funcionan los umbrales:**

- `relevance_threshold`: Filtra contenido de baja relevancia (0.0 = basura, 1.0 = altamente relevante)
- Los insights con `relevance_score < threshold` no aparecen en el Markdown
- El JSON completo siempre preserva TODOS los datos sin filtrado

## 📖 Uso

### Ejemplos Básicos

```bash
# Análisis genérico de PDF (sin contexto de dominio)
python main.py documento.pdf

# Procesar presentación PowerPoint (auto-convierte a PDF)
python main.py presentacion.pptx

# Con prompts específicos del sector AFP chileno
python main.py informe_afp.pdf --domain-prompts afp_chile

# Procesar PPTX con contexto de dominio
python main.py reporte_afp.pptx --domain-prompts afp_chile

# Con configuración personalizada (ej: API keys, filtros personalizados)
python main.py documento.pdf --config private_config.json

# Procesar múltiples archivos (wildcards)
python main.py *.pdf --domain-prompts afp_chile
python main.py *.pptx --domain-prompts finanzas

# Exportar también a formato Word (.docx)
python main.py reporte.pdf --export-docx

# Combinando todas las opciones
python main.py presentacion.pptx --config custom.json --domain-prompts finanzas --export-docx
# Combinando todas las opciones
python main.py presentacion.pptx --config custom.json --domain-prompts finanzas --export-docx

# Solo hallazgos cuantitativos (sin hipótesis ni observaciones)
# Editar config.json: "insight_filter": "findings"
python main.py estudio.pdf --config config.json
```

### Argumentos Disponibles

```
python main.py <archivo(s)> [opciones]

Argumentos posicionales:
  archivo(s)               Ruta(s) al PDF o PPTX a procesar
                          Acepta múltiples archivos o wildcards (*.pdf, *.pptx)

Opciones:
  --config PATH            Ruta al archivo de configuración
                          (default: config.json)
  
  --domain-prompts NOMBRE  Nombre del archivo de prompts de dominio
                          Se busca en prompts/domains/
                          Ejemplo: afp_chile (busca afp_chile.md)
  
  --export-docx            Exportar también a tabla Word (.docx)
                          Genera un inventario de conclusiones en formato tabla
```

**Nota sobre PPTX:** Los archivos PowerPoint se convierten automáticamente a PDF antes del análisis. Requiere LibreOffice o PowerPoint instalado (ver sección de instalación).

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
├── output/                        # Directorio de salida
    ├── images/                    # Imágenes extraídas y filtradas
    ├── text/                      # Texto extraído por página
    └── data/                      # Análisis completo
        ├── documento_analysis.ndjson       # Claims en formato NDJSON
        ├── documento_analysis.docx         # Tabla Word (opcional)
        └── insights-documento.md           # Resumen legible filtrado
```

## 🔍 Ejemplo de Salida

El sistema genera tres tipos de archivos:

### 1. NDJSON (datos estructurados)

Un JSON por línea con registros meta/claim/summary:

```ndjson
{"type":"meta","study":{"study_name":"documento.pdf","report_date":null},"extraction":{...}}
{"type":"claim","id":"C001","page_number":5,"classification":"finding","claim_text":"...","evidence":{...}}
{"type":"claim","id":"C002","page_number":5,"classification":"hypothesis","claim_text":"...","evidence":{...}}
{"type":"summary","counts":{"findings":8,"hypotheses":15,"methodological_notes":2},...}
```

Cada claim incluye:
- `id`: Identificador único (C001, C002...)
- `classification`: `"finding"` | `"hypothesis"` | `"methodological_note"`
- `evidence`: `{n, data_type, base_label}`
- `theme_tags`: Etiquetas temáticas
- `ambiguity_flags`: Indicadores de limitaciones (missing_base, low_n_referential, etc.)

### 2. Tabla Word (.docx) - Opcional

Tabla estructurada para inventario de conclusiones:

| ID | Página | Fecha | Estudio | Tipo | Conclusión | Datos (N) | Evidencia / limitaciones |
|----|--------|-------|---------|------|------------|-----------|--------------------------|
| C001 | p.5 | 2025-01-13 | documento.pdf | Hallazgo | Satisfacción neta de 68 puntos | N=1260; Cuantitativo | Relevancia: 0.85 |

Para habilitar:
```bash
# Por línea de comandos
python main.py documento.pdf --export-docx

# O en config.json
"analysis": {
  "export_docx": true
}
```

### 3. Resumen Markdown (filtrado)

Archivo legible para humanos con insights filtrados:

```markdown
# Insights - documento.pdf

**Fecha de análisis**: 2026-01-13 14:32
**Total páginas**: 56 | **Gráficos analizados**: 12
**Filtro**: Hallazgos + Hipótesis (sin observaciones) | **Umbral relevancia**: 0.5

> 📊 **Hallazgo**: Respaldado por datos cuantitativos (N alto)  
> 💡 **Hipótesis**: Exploratorio o cualitativo (requiere validación)  
> 📝 **Observación**: Descripción metodológica/contextual

## Insights de Gráficos

### 1. Evolución de Satisfacción (línea)

- 📊 **[Hallazgo]** (N=1260) Satisfacción neta alcanza 68 puntos, +5pp vs semestre anterior
- 💡 **[Hipótesis]** La mejora se asocia a reducción de reclamos en atención telefónica

---

**Resumen**: 8 hallazgos | 15 hipótesis
```

**Control del contenido:** Ajusta `relevance_threshold` (0-1) e `insight_filter` en `config.json` para personalizar qué aparece en el resumen.

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
class InsightItem(BaseModel):
    """Insight con clasificación automática"""
    text: str
    classification: Literal["finding", "hypothesis", "observation"]
    sample_size: Optional[int]
    evidence_type: Optional[Literal["quantitative", "qualitative", "mixed"]]

class ChartData(BaseModel):
    chart_type: str
    title: str
    insights: List[InsightItem]  # Lista de insights clasificados
    relevance_score: float        # Score 0-1 para filtrado
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

## 🎯 Control de Calidad de Insights

### Sistema de Relevancia

Cada análisis (gráfico o texto) recibe un `relevance_score` de 0 a 1:

| Score | Descripción | Ejemplo |
|-------|-------------|---------|
| **0.7-1.0** | Alta relevancia - Datos cuantitativos, métricas clave | Gráfico con KPIs, tabla con resultados de encuesta |
| **0.4-0.7** | Relevancia media - Información descriptiva útil | Contexto cualitativo, explicaciones metodológicas |
| **0.0-0.4** | Baja relevancia - Contenido decorativo o sin valor | Logos, banners, páginas de portada, texto legal |

**Configurar el umbral:**

```json
{
  "analysis": {
    "relevance_threshold": 0.5  // Solo insights ≥ 0.5 en el resumen
  }
}
```

### Sistema de Clasificación

Cada insight se clasifica automáticamente por la IA:

#### 📊 Finding (Hallazgo)
- **Cuándo**: Datos cuantitativos con N ≥ 100, encuestas representativas
- **Ejemplo**: "N=1260 casos muestran satisfacción de 68%, +5pp vs semestre anterior"
- **Valor**: Alto - Conclusiones generalizables con respaldo estadístico

#### 💡 Hypothesis (Hipótesis)
- **Cuándo**: Observaciones cualitativas, N < 50, interpretaciones exploratorias
- **Ejemplo**: "Los usuarios reportan confusión con el proceso de afiliación"
- **Valor**: Medio - Requiere validación adicional

#### 📝 Observation (Observación)
- **Cuándo**: Información metodológica, contexto del estudio, descripciones procedimentales
- **Ejemplo**: "El estudio utiliza encuestas telefónicas en comunas urbanas con población >130K"
- **Valor**: Documental - No es una conclusión, solo describe cómo se hizo el estudio

### Filtrado Recomendado

Para análisis ejecutivo, usa:

```json
{
  "analysis": {
    "relevance_threshold": 0.6,       // Filtro más estricto
    "insight_filter": "actionable",   // Excluye observaciones metodológicas
    "show_insight_classification": true
  }
}
```

Esto elimina:
- ❌ Contenido decorativo (logos, banners)
- ❌ Descripciones metodológicas ("El estudio abarca...")
- ❌ Información procedimental sin insights
- ✅ Mantiene solo hallazgos y conclusiones accionables

### Casos de Uso por Filtro

| `insight_filter` | Uso Recomendado |
|------------------|-----------------|
| `"actionable"` | **Reportes ejecutivos** - Solo conclusiones útiles |
| `"findings"` | **Análisis cuantitativo** - Solo datos con respaldo estadístico |
| `"all"` | **Documentación completa** - Incluye contexto metodológico |
| `"hypotheses"` | **Exploración cualitativa** - Solo observaciones interpretativas |

**Tip**: El JSON siempre contiene TODOS los datos. Los filtros solo afectan el resumen Markdown.