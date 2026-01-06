# Sistema de Prompts Modular

Este directorio contiene los prompts que guían el análisis de gráficos con IA, organizados en dos niveles: instrucciones base (genéricas) y contextos de dominio (especializados).

## 🗂️ Estructura

```
prompts/
├── base_chart_analysis.md      # Prompt base (genérico, para cualquier gráfico)
├── base_text_analysis.md       # Análisis de texto (opcional)
├── domains/                     # Contextos específicos por sector/empresa
│   ├── afp_chile.md            # Sector AFP Chile
│   └── [tu_dominio].md         # Tus contextos personalizados
└── README.md                    # Esta guía
```

## 🔄 Cómo Funciona

### Nivel 1: Prompt Base (`base_chart_analysis.md`)

**Propósito**: Instrucciones universales de análisis aplicables a cualquier gráfico

**Contiene**:
- Metodología de análisis paso a paso
- Formato de respuesta estructurado (JSON/Pydantic)
- Principios de precisión y completitud
- Manejo de casos especiales

**Cuándo modificar**: 
- Cambiar estructura de salida (modelo Pydantic)
- Ajustar metodología general de análisis
- Mejorar instrucciones universales

### Nivel 2: Contexto de Dominio (`domains/*.md`)

**Propósito**: Conocimiento específico del negocio/industria

**Contiene**:
- Terminología especializada del sector
- Métricas relevantes y sus fórmulas
- Convenciones de presentación
- Ejemplos de interpretación contextualizada
- Glosarios y referencias

**Cuándo crear uno nuevo**:
- Analizar documentos de un nuevo sector/empresa
- Necesitas terminología específica
- Requieres interpretación contextualizada de métricas

## 📝 Uso del Sistema

### Modo 1: Análisis Genérico (sin dominio)

```bash
python main.py documento.pdf
```

**El modelo recibe**:
- ✅ Prompt base (`base_chart_analysis.md`)
- ❌ Sin contexto específico

**Ideal para**: Documentos de sectores diversos o análisis exploratorio

### Modo 2: Análisis Especializado (con dominio)

```bash
python main.py informe_afp.pdf --domain-prompts afp_chile
```

**El modelo recibe**:
- ✅ Prompt base (`base_chart_analysis.md`)
- ✅ Contexto de dominio (`domains/afp_chile.md`)

**Ideal para**: Documentos de un sector específico con terminología técnica

## Mejores Prácticas

### ✅ Hacer
- Separar instrucciones generales (base) de conocimiento específico (dominio)
- Usar ejemplos concretos en contextos de dominio
- Actualizar terminología cuando cambie el sector
- Documentar métricas específicas y sus fórmulas
- Incluir glosarios y referencias

### ❌ Evitar
- Duplicar instrucciones entre base y dominio
- Hardcodear nombres de empresas específicas (usar sector/industria)
- Instrucciones contradictorias entre base y dominio
- Contextos demasiado largos (>3000 palabras)

## Plantilla para Nuevo Dominio

```markdown
# Contexto de Dominio: [Nombre del Sector/Empresa]

## Contexto del Negocio
[Descripción breve de la industria/empresa]

## Terminología Clave del Sector
- **Término 1**: Definición
- **Término 2**: Definición

## Métricas Relevantes
- Métrica A: qué mide, cómo se calcula
- Métrica B: qué mide, cómo se calcula

## Tipos de Análisis Comunes
1. Tipo de análisis 1
2. Tipo de análisis 2

## Formato de Valores
- Cómo se presentan las cifras
- Unidades de medida comunes

## Insights Importantes para Este Sector
- Qué buscar en los datos
- Qué patrones son significativos

## Ejemplo de Buen Análisis
[Ejemplo concreto del sector]

## Instrucciones Especiales
- Consideraciones específicas al analizar este tipo de documentos
```

## Mantenimiento

- **Revisar periódicamente**: Los dominios evolucionan, actualizar terminología
- **Agregar ejemplos**: Cuando encuentres buenos análisis, agrégalos como ejemplos
- **Optimizar longitud**: Mantener balance entre completitud y brevedad
- **Validar resultados**: Si el agente produce errores consistentes, revisar instrucciones

## Troubleshooting

**Problema**: Agente genera análisis incorrectos
- ✓ Verificar que estás usando `--domain-prompts` correctamente
- ✓ Revisar si la terminología del contexto está actualizada
- ✓ Agregar ejemplos específicos en el archivo de dominio

**Problema**: Agente ignora formato de salida
- ✓ Revisar que `base_chart_analysis.md` tenga instrucciones claras
- ✓ Verificar que el schema de salida (ChartData en `models.py`) coincida

**Problema**: Análisis demasiado genérico
- ✓ Asegurar que usas `--domain-prompts` en el comando CLI
- ✓ Enriquecer el archivo de dominio con más contexto y ejemplos

**Problema**: Dominio no se carga
- ✓ Verificar que el archivo existe en `prompts/domains/`
- ✓ El nombre debe ser exacto (case-sensitive)
- ✓ La extensión `.md` es opcional en CLI: `--domain-prompts afp_chile`

## 🚀 Guía Rápida: Crear Tu Primer Dominio

1. **Crea** `prompts/domains/mi_sector.md`
2. **Copia** la plantilla de arriba y completa con tu información
3. **Usa**: `python main.py doc.pdf --domain-prompts mi_sector`
4. **Itera**: Revisa resultados y mejora el contexto
