from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime


class InsightItem(BaseModel):
    """Un insight/claim individual con clasificación y metadatos para trazabilidad"""
    text: str = Field(description="El texto del insight (paráfrasis fiel)")
    classification: Literal["finding", "hypothesis", "methodological_note"] = Field(
        default="hypothesis", 
        description="'finding' si está respaldado por datos cuantitativos con N alto (≥100), 'hypothesis' si es exploratorio/cualitativo o N bajo, 'methodological_note' si es descripción metodológica/contextual"
    )
    sample_size: Optional[int] = Field(
        None, 
        description="Tamaño de muestra (N) si se menciona o puede inferirse. No inventar."
    )
    evidence_type: Optional[Literal["quantitative", "qualitative", "mixed", "unknown"]] = Field(
        None, 
        description="Tipo de evidencia: 'quantitative' (encuestas, datos estadísticos), 'qualitative' (focus groups, entrevistas), 'mixed', 'unknown'"
    )
    # Nuevos campos para trazabilidad y validación
    ambiguity_flags: List[str] = Field(
        default_factory=list,
        description="Flags de ambigüedad: 'missing_base', 'low_n_referential', 'unspecified_method', 'inferred_n', etc."
    )
    theme_tags: List[str] = Field(
        default_factory=list,
        description="Tags temáticos: 'satisfacción', 'NPS', 'canales', 'tiempos', 'ranking', 'problemas', etc."
    )
    classification_rationale: Optional[str] = Field(
        None,
        description="Explicación breve de por qué se clasificó así (especialmente si es hipótesis por falta de N)"
    )


class ChartResource(BaseModel):
    """Información del recurso de origen del gráfico"""
    type: str = Field(description="Tipo de visualización (barra, línea, pie, tabla, matriz, etc.)")
    resource: str = Field(description="Ruta al archivo de imagen")
    resource_type: str = Field(default="image", description="Tipo de recurso")


class ChartAnalysisResult(BaseModel):
    """Resultado del análisis de IA (sin información de recurso)"""
    chart_type: str = Field(description="Tipo de visualización (barra, línea, pie, tabla, matriz, etc.)")
    title: Optional[str] = Field(None, description="Título de la visualización")
    description: Optional[str] = Field(None, description="Descripción de lo que muestra")
    categories: List[str] = Field(default_factory=list, description="Categorías o labels")
    series: List[Dict[str, Any]] = Field(default_factory=list, description="Series de datos")
    values: List[float] = Field(default_factory=list, description="Valores numéricos")
    insights: List[InsightItem] = Field(default_factory=list, description="Insights clasificados como hallazgos o hipótesis")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Métricas calculadas")
    relevance_score: float = Field(default=0.5, ge=0, le=1, description="Puntuación de relevancia (0-1). 0=sin valor, 1=muy relevante. Imágenes decorativas, logos o sin datos útiles deben tener score bajo.")


class ChartData(BaseModel):
    """Datos extraídos de un gráfico o tabla"""
    chart_data: ChartResource = Field(description="Información del recurso y tipo de gráfico")
    title: Optional[str] = Field(None, description="Título de la visualización")
    description: Optional[str] = Field(None, description="Descripción de lo que muestra")
    categories: List[str] = Field(default_factory=list, description="Categorías o labels")
    series: List[Dict[str, Any]] = Field(default_factory=list, description="Series de datos")
    values: List[float] = Field(default_factory=list, description="Valores numéricos")
    insights: List[InsightItem] = Field(default_factory=list, description="Insights clasificados como hallazgos o hipótesis")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Métricas calculadas")
    relevance_score: float = Field(default=0.5, ge=0, le=1, description="Puntuación de relevancia (0-1)")


class TextAnalysis(BaseModel):
    """Análisis estructurado de texto con IA"""
    key_metrics: Dict[str, Any] = Field(default_factory=dict, description="Métricas clave extraídas")
    percentages: List[Dict[str, Any]] = Field(default_factory=list, description="Porcentajes con contexto")
    dates: List[str] = Field(default_factory=list, description="Fechas mencionadas")
    entities: Dict[str, List[str]] = Field(default_factory=dict, description="Entidades (empresas, productos, personas)")
    insights: List[InsightItem] = Field(default_factory=list, description="Insights clasificados como hallazgos o hipótesis")
    keywords: List[str] = Field(default_factory=list, description="Palabras clave")
    relevance_score: float = Field(default=0.5, ge=0, le=1, description="Puntuación de relevancia (0-1). 0=sin valor/ruido, 1=muy relevante. Páginas sin contenido útil o con errores de extracción deben tener score bajo.")


class TextData(BaseModel):
    """Datos extraídos del texto"""
    page_number: int
    content: str
    key_metrics: Dict[str, Any] = Field(default_factory=dict, description="Métricas clave encontradas")
    dates: List[str] = Field(default_factory=list, description="Fechas mencionadas")
    percentages: List[float] = Field(default_factory=list, description="Porcentajes encontrados")
    keywords: List[str] = Field(default_factory=list, description="Palabras clave")
    ai_analysis: Optional[TextAnalysis] = Field(None, description="Análisis con IA (si está habilitado)")


class ImageData(BaseModel):
    """Metadatos de imagen extraída"""
    filename: str
    page_number: int
    path: str
    width: int
    height: int
    extracted_at: datetime = Field(default_factory=datetime.now)
    # Campos para gráficos compuestos (imagen + texto renderizado separado)
    bbox: Optional[List[float]] = Field(None, description="Bounding box [x0, y0, x1, y1] en coordenadas de página")
    context_text: Optional[str] = Field(None, description="Texto cercano a la imagen (para gráficos compuestos)")
    is_composite: bool = Field(False, description="True si se detectó como gráfico compuesto")


class DocumentAnalysis(BaseModel):
    """Análisis completo de un documento"""
    filename: str
    total_pages: int
    extraction_date: datetime = Field(default_factory=datetime.now)
    text_data: List[TextData] = Field(default_factory=list)
    image_data: List[ImageData] = Field(default_factory=list)
    chart_analysis: List[ChartData] = Field(default_factory=list)
    summary: Optional[str] = None


class Config(BaseModel):
    """Configuración del sistema"""
    extraction: Dict[str, Any]
    analysis: Dict[str, Any]
    prompts: Dict[str, Any]
