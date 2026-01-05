# Sistema de Prompts Modular

Este directorio contiene los prompts que guían el análisis de gráficos con IA, separados en dos niveles:

## Estructura

```
prompts/
├── base_chart_analysis.md      # Prompt base (genérico, para cualquier gráfico)
├── domains/                     # Contextos específicos por dominio/empresa
│   ├── afp_chile.md            # Contexto para AFPs chilenas
│   ├── generic.md              # Contexto empresarial genérico
│   └── [otros dominios...]     # Agregar según necesidad
└── README.md                    # Este archivo
```

## Cómo Funciona

### 1. Prompt Base (`base_chart_analysis.md`)
**Propósito**: Instrucciones generales de análisis aplicables a cualquier gráfico

**Contiene**:
- Metodología de análisis paso a paso
- Formato de respuesta estructurado (JSON)
- Principios de precisión y completitud
- Manejo de casos especiales

**Cuándo modificar**: 
- Cambiar estructura de salida (schema)
- Ajustar metodología de análisis
- Mejorar instrucciones generales

### 2. Contexto de Dominio (`domains/*.md`)
**Propósito**: Conocimiento específico del negocio/industria

**Contiene**:
- Terminología especializada
- Métricas relevantes del sector
- Convenciones de presentación
- Ejemplos de interpretación contextualizada
- Glosarios y referencias

**Cuándo modificar**:
- Analizar documentos de una nueva empresa/sector
- Actualizar terminología del dominio
- Agregar nuevas métricas relevantes

## Configuración en `config.json`

```json
{
  "prompts": {
    "prompts_dir": "prompts",
    "base_prompt": "base_chart_analysis.md",
    "domain": "afp_chile",  // Cambiar según el caso
    "domain_prompts": {
      "afp_chile": "afp_chile.md",
      "generic": "generic.md"
      // Agregar más dominios aquí
    }
  }
}
```

## Cómo Agregar un Nuevo Dominio

### Paso 1: Crear archivo de contexto
Crea `prompts/domains/mi_empresa.md` con:
- Contexto del negocio
- Terminología clave
- Métricas relevantes
- Tipos de análisis comunes
- Ejemplos específicos

### Paso 2: Registrar en config.json
```json
"domain_prompts": {
  "afp_chile": "afp_chile.md",
  "generic": "generic.md",
  "mi_empresa": "mi_empresa.md"  // Agregar aquí
}
```

### Paso 3: Activar en config.json
```json
"domain": "mi_empresa"  // Cambiar aquí
```

## Ejemplo de Uso

### Para AFP Chilena (actual)
```json
"domain": "afp_chile"
```
El agente recibirá:
- ✓ Instrucciones base de análisis
- ✓ Contexto de AFPs (fondos A-E, rentabilidad, etc.)

### Para Empresa Genérica
```json
"domain": "generic"
```
El agente recibirá:
- ✓ Instrucciones base de análisis
- ✓ Contexto empresarial general (KPIs, finanzas, etc.)

### Sin Contexto de Dominio
```json
"domain": null
```
El agente recibirá:
- ✓ Solo instrucciones base de análisis
- ✗ Sin contexto especializado

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
- ✓ Verificar que el dominio correcto esté seleccionado
- ✓ Revisar si la terminología del contexto está actualizada
- ✓ Agregar ejemplos específicos en el archivo de dominio

**Problema**: Agente ignora formato de salida
- ✓ Revisar que `base_chart_analysis.md` tenga instrucciones claras
- ✓ Verificar que el schema de salida (ChartData) coincida con las instrucciones

**Problema**: Análisis demasiado genérico
- ✓ Asegurar que `domain` no sea `null` en config.json
- ✓ Enriquecer el archivo de dominio con más contexto específico
