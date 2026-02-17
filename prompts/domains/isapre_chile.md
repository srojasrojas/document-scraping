# Contexto de Dominio: Isapres (Instituciones de Salud Previsional) - Chile

## Contexto del Negocio

Las **isapres** son aseguradoras privadas de salud que administran cotizaciones de salud (principalmente el **7% legal** y cotizaciones adicionales) para financiar prestaciones médicas de sus afiliados y cargas. Operan mediante **planes de salud** (con precios usualmente en **UF**) que determinan **coberturas, redes, bonificaciones, copagos, topes** y condiciones (p. ej., CAEC, GES). Este contexto te ayudará a interpretar correctamente métricas, tablas y gráficos típicos del sector.

## Terminología Clave del Sector

### Productos, Coberturas y Modalidades

- **Plan de Salud**: Contrato que define precio (UF), cobertura, red, topes, deducibles y condiciones.
- **Cotización legal (7%)**: Porcentaje de remuneración imponible destinado a salud.
- **Cotización adicional**: Monto extra que el afiliado paga sobre el 7% para financiar un plan más caro o mejores coberturas.
- **Beneficiarios**: **Cotizante** + **cargas** (dependientes).
- **Red de Prestadores / Preferentes**: Prestadores con convenio; suele mejorar bonificación y/o reducir copago.
- **Modalidad Libre Elección**: Permite atenderse fuera de red, generalmente con menor bonificación o mayores topes.
- **Bonificación**: % o $ que cubre la isapre sobre el valor de la prestación.
- **Copago**: Monto que paga el afiliado (lo no bonificado).
- **Tope / Máximo bonificable**: Límite de cobertura por prestación, evento o anual.
- **Deducible**: Monto que el afiliado debe pagar antes de que opere cierta cobertura (frecuente en CAEC).
- **Carencia / Espera**: Período en que ciertas coberturas no aplican (según plan/beneficio).
- **Preexistencias**: Condiciones de salud previas (históricamente relevantes; el tratamiento normativo puede variar).
- **GES (Garantías Explícitas en Salud / AUGE)**: Beneficios garantizados para problemas de salud definidos; incluye acceso, oportunidad, protección financiera y calidad.
- **Prima GES (o Precio GES)**: Cargo asociado a financiar el componente GES del plan (puede estar separado o integrado).
- **CAEC (Cobertura Adicional para Enfermedades Catastróficas)**: Beneficio para eventos de alto costo bajo reglas específicas (red, deducible, topes).

### Métricas Relevantes (Operacionales y Financieras)

- **Cartera de beneficiarios**: Total de beneficiarios; a veces separa cotizantes y cargas.
- **Ingresos por cotizaciones**: Principal ingreso (7% + adicional).
- **Ingresos/Costos GES**: Componentes asociados al GES (según presentación).
- **Costo de prestaciones**: Gasto en atenciones médicas bonificadas (ambulatorio, hospitalario, etc.).
- **Licencias médicas (SIL)**: Puede aparecer como costo relevante según el reporte.
- **Siniestralidad**: Relación entre costos (prestaciones y/o SIL) e ingresos por cotizaciones/primas.
- **Costo médico per cápita**: Costo de prestaciones dividido por beneficiarios (o por cotizantes).
- **Frecuencia de uso**: Prestaciones por beneficiario (consultas, exámenes, hospitalizaciones).
- **Severidad**: Costo promedio por prestación/evento (p. ej., costo por hospitalización).
- **Resultado técnico**: Resultado del negocio asegurador (según definición del informe).
- **Gastos de administración (OPEX)**: Costos operativos de la isapre.
- **Margen operacional / EBITDA / Resultado neto**: Métricas de rentabilidad según estados financieros.
- **Patrimonio / Solvencia**: Capital y capacidad de cumplir obligaciones.
- **Reservas / Provisiones técnicas**: Pasivos estimados por obligaciones (según normativa).
- **Adecuación/Reajuste de precios**: Ajustes del precio base del plan (marco regulatorio vigente).
- **ICSA (Indicador de Costos de la Salud)**: Referencia regulatoria para variaciones de costos del sistema (cuando aplique).
- **Judicialización**: Impacto de fallos, recursos y devoluciones (si el documento lo trata).

### Indicadores del Sistema (Contexto Externo)

- **UF**: Unidad de Fomento (común en precios de planes, topes y deducibles).
- **IPC / IPC Salud**: Inflación general y/o componente salud (para contexto de costos).
- **Envejecimiento de cartera**: Cambios en mix etario afectan costos.
- **Estructura de prestaciones**: Mix ambulatorio vs hospitalario; impacto de tecnologías y precios.

### Actores del Sistema

- **Isapre**: Aseguradora privada de salud.
- **SIS (Superintendencia de Salud)**: Regulador.
- **Afiliado/Cotizante**: Titular del plan.
- **Cargas/Beneficiarios**: Dependientes del cotizante.
- **Prestadores**: Clínicas, hospitales, médicos, laboratorios, centros.
- **Fonasa**: Seguro público (referencia competitiva y de movilidad del sistema).
- **COMPIN / SUSESO**: Actores relevantes en licencias médicas (según el enfoque del documento).

## Tipos de Análisis Comunes

1. **Comparación entre isapres**: cartera, ingresos, siniestralidad, resultado, solvencia.
2. **Evolución temporal**: crecimiento/caída de beneficiarios, variación de costos, siniestralidad y márgenes.
3. **Análisis de costos médicos**: frecuencia vs severidad; mix ambulatorio/hospitalario; gasto per cápita.
4. **Análisis de precios del plan**: precio en UF, adecuaciones, prima GES, relación precio/cobertura.
5. **Participación de mercado**: cuota de beneficiarios/cotizantes por isapre.
6. **Gestión de riesgo**: concentración por edad/sexo, enfermedades de alto costo, impacto de CAEC/GES.
7. **Red y utilización**: uso de prestadores preferentes vs libre elección; cambios de red.
8. **Licencias médicas**: tendencias, costo, medidas de control (si aplica).

## Convenciones de Presentación

### Formato de Valores

- **Precios de planes / deducibles / topes**: frecuentemente en **UF** (a veces $).
- **Ingresos/costos**: $ (millones, miles de millones) o UF; especificar unidad.
- **Bonificación**: en % (ej: 80% red preferente) o en $ con tope.
- **Copago**: $ o UF.
- **Fechas**: dd/mm/aaaa o “2023”, “1T 2024”, “últimos 12 meses (LTM)”.

### Gráficos y Códigos Visuales Típicos

- Barras comparativas por isapre (cartera, siniestralidad, resultado).
- Series de tiempo (costo per cápita, siniestralidad, beneficiarios).
- “Mix” en torta o barras apiladas (ambulatorio/hospitalario, GES/no GES, red/no red).
- Tablas de planes (precio UF, cobertura, deducible CAEC, topes).

## Contexto para Interpretación

### Qué Buscar en los Gráficos

1. **Cartera (beneficiarios/cotizantes)**
   - Tendencia (crece/cae), estacionalidad, quiebres por cambios regulatorios o precios.
   - Mix (edad, cargas por cotizante) si está disponible.

2. **Costos y siniestralidad**
   - Si el costo incluye solo prestaciones o también licencias médicas.
   - Relación costos/ingresos: si sube siniestralidad, suele presionar márgenes.
   - Identificar si el aumento proviene de **frecuencia** (más uso) o **severidad** (más caro).

3. **Precio del plan y GES/CAEC**
   - Separar: precio base vs prima GES (si el documento lo desagrega).
   - Ver reglas de CAEC (deducible, red obligatoria) que cambian el gasto de bolsillo.

4. **Rentabilidad y solvencia**
   - Diferenciar resultado operacional vs neto (efectos no recurrentes, provisiones).
   - Señales de estrés: pérdidas persistentes, deterioro patrimonial, cambios en provisiones.

5. **Comparaciones**
   - Ranking y brechas: “X pp” en siniestralidad, “UF Y” en precio promedio, etc.
   - Comparar contra promedio de la industria cuando exista.

### Insights Importantes para Este Sector

Al analizar documentos, prioriza:

- **Accesibilidad financiera**: copagos esperados, deducibles y topes (riesgo de gasto de bolsillo).
- **Sostenibilidad**: evolución de siniestralidad y resultado técnico.
- **Eficiencia**: gasto admin por beneficiario, control de costos, uso de red preferente.
- **Riesgo de cartera**: envejecimiento, aumento de cargas, concentración en altos costos.
- **Efectos regulatorios/judiciales**: si el documento menciona impactos en precios, devoluciones o provisiones.

## Fórmulas y Cálculos Comunes (orientativas; depende del informe)

```txt
Copago ($) = Valor de la prestación - Bonificación Isapre

Bonificación (%) = Bonificación Isapre / Valor de la prestación

Siniestralidad (%) = Costos asistenciales / Ingresos por cotizaciones
  (a veces: (Prestaciones + SIL) / Ingresos, según definición del documento)

Costo per cápita = Costos asistenciales / Nº beneficiarios

Variación (%) = (Valor_t / Valor_{t-1} - 1) × 100
```

## Ejemplo de Análisis Contextualizado

**Mal análisis** (sin contexto):
> "El gráfico muestra que algunas isapres tienen barras más altas que otras."

**Buen análisis** (con contexto):
> "Siniestralidad LTM por isapre. La Isapre A presenta 92%, 6 pp sobre el promedio del sistema (86%), lo que sugiere presión en margen técnico si no hay ajustes de precio o contención de costos. En paralelo, su costo per cápita sube 12% interanual, explicado principalmente por mayor severidad hospitalaria (alza del costo promedio por evento) más que por frecuencia."

## Referencias y Fuentes Típicas

Los documentos pueden incluir datos de:
- **Superintendencia de Salud (SIS)**: Estadísticas oficiales del sistema isapre.
- **Estados financieros / Memorias anuales de isapres**: Reportes corporativos con balance, siniestralidad, provisiones.
- **Informes de la industria**: Consultoras, asociaciones (p. ej., ACISAPRES), centros de estudio.
- **MINSAL / GES**: Cambios en garantías de salud, canastas de servicios, impacto en costos.
- **SUSESO / COMPIN**: Datos de licencias médicas (SIL) y su variación.
- **BCCh / INE**: UF, IPC, contexto macroeconómico e inflación de costos de salud.
- **Fallos judiciales / SERNAC**: Devoluciones, cambios en coberturas (afecta provisiones y resultado).

## Instrucciones Especiales (para analizar documentos de isapres)

Cuando analices gráficos y datos de este dominio:

1. **Identifica unidades**: Diferencia UF vs $ (pesos) y período (mensual, trimestral, anual, LTM).
2. **Aclara definiciones**: Qué incluye exactamente "costos" (solo prestaciones vs prestaciones + GES/CAEC + SIL).
3. **Distingue precio vs cobertura**: Un plan más caro (UF) puede ofrecer mayor bonificación, topes más altos o red más amplia.
4. **Explica copagos y riesgo de bolsillo**: Deducibles (especialmente CAEC), topes, diferencias red preferente vs libre elección.
5. **Contextualiza cambios**: Identifica quiebres por regulación, fallos, adecuaciones de precio, cambios de red, cambios epidemiológicos.
6. **Cuantifica brechas**: Expresa diferencias en pp (siniestralidad), UF (precio), $ (costos), % (variación).
7. **Evita suposiciones**: Si el documento no define siniestralidad, no separa GES de prestaciones, o no especifica el período, indícalo explícitamente.
8. **Conecta operaciones con finanzas**: Cambios en frecuencia/severidad → impacto en siniestralidad → presión en margen → decisiones de precio/contención.

## Glosario Rápido

| Término | Significado |
|---------|-------------|
| Isapre | Aseguradora privada de salud en Chile |
| SIS | Superintendencia de Salud (regulador) |
| UF | Unidad de Fomento (indexada a inflación chilena) |
| GES / AUGE | Garantías Explícitas en Salud (beneficios garantizados) |
| Prima GES | Cargo para financiar la cobertura GES (según plan) |
| CAEC | Cobertura Adicional para Enfermedades Catastróficas |
| Bonificación | Porcentaje o monto que cubre la isapre |
| Copago | Monto pagado por el afiliado (no bonificado) |
| Tope | Límite máximo de cobertura por prestación o anual |
| Deducible | Monto que el afiliado paga antes de activar un beneficio |
| Siniestralidad | Costos asistenciales / ingresos por cotizaciones (%) |
| Costo per cápita | Gasto en prestaciones / número de beneficiarios |
| Frecuencia | Cantidad de prestaciones por beneficiario |
| Severidad | Costo promedio por prestación/evento |
| SIL | Subsidio por Incapacidad Laboral (licencias médicas) |
| OPEX | Gastos de administración y operación |
| Margen técnico | Ingresos por cotizaciones - Costos (antes de OPEX) |
| pp | Puntos porcentuales (diferencia entre porcentajes) |
| LTM | Last Twelve Months (últimos 12 meses) |
| Red preferente | Prestadores con convenio (mejor bonificación/copago) |
| Libre elección | Atención fuera de red (menor bonificación, mayor copago) |
