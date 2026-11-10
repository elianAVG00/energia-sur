# Energía Sur — Integración de la fuente ENRE para CU01

> **Estado:** guía técnica para agentes de IA; **investigación documental completada y contrato bruto validado en vivo el 2026-11-10**.  
> **Fecha de revisión:** 2026-11-10 (Argentina).  
> **Decisión humana aprobada:** ENRE es la **fuente primaria provisional** de CU01; el recurso real ya fue validado (ver sección 8 y `openspec/changes/archive/2026-11-10-implement-current-outages-cu01/`).  
> **Alcance:** CU01 — Consultar cortes actuales en una zona. No autoriza implementar, modificar el repositorio ni ejecutar OpenSpec Sync/Archive.

## 0. Instrucciones obligatorias para el agente

1. Distinguir siempre **[VERIFICADO]**, **[ANTECEDENTE]**, **[PROPUESTA]** y **[PENDIENTE]**. No elevar los ejemplos o referencias históricas a contrato actual.
2. Primero leer `AGENTS.md`, `docs/STATE.md`, `docs/use-cases/` y OpenSpec del repositorio. Este documento es un **insumo técnico**, no reemplaza los requisitos acordados.
3. No considerar un `HTTP 200` prueba suficiente: comprobar estructura, registros, coherencia, fecha de actualización, codificación y posibilidad de normalizar.
4. No ejecutar JavaScript remoto ni usar `eval`; los datos publicados por terceros no son código confiable.
5. No afirmar que un domicilio tiene o no electricidad a partir de un dato por partido/localidad. Tampoco interpretar una respuesta vacía o una fuente caída como «sin cortes».
6. No inventar IDs estables, coordenadas ni timestamps ausentes. Evitar scraping de HTML si el recurso bruto es utilizable.
7. No confundir cortes actuales (CU01), trabajos futuros (CU02) y administración de actualizaciones (CU10).

## 1. Fuentes oficiales y direcciones

| Propósito | Método | URL | Estado y uso |
|---|---|---|---|
| **Datos brutos Edesur (ENRE)** | `GET` | `https://www.enre.gov.ar/paginacorte/js/data_EDS.js` | **Fuente primaria propuesta**. Recurso JavaScript de consumo público usado por la página de cortes; **no** API JSON oficialmente versionada. |
| Página de cortes de Edesur (ENRE) | `GET` | `https://www.enre.gov.ar/paginacorte/tabla_cortes_edesur.html` | Página oficial para contraste visual, categorías y frecuencia declarada; renderizada mediante JavaScript. |
| Página institucional ENRE | `GET` | `https://www.argentina.gob.ar/enre/estado-del-servicio-electrico-de-edesur` | Página gubernamental que incorpora la vista del ENRE por `iframe`; referencia para el usuario. |
| Mapa de cortes ENRE | `GET` | `https://www.enre.gov.ar/mapacortes/index.html` | Referencia oficial adicional; no asumir que usa el mismo contrato de datos sin comprobarlo. |
| Datos de Edenor, **fuera de alcance** | `GET` | `https://www.enre.gov.ar/paginacorte/js/data_EDN.js` | Referencia análoga; CU01 se concentra en el área de Edesur. |

**[VERIFICADO]** La página oficial del ENRE declara actualizaciones **cada cinco minutos**. Es una frecuencia declarada para la publicación, **no SLA**, garantía de latencia ni una hora de actualización comprobada del recurso bruto en esta revisión.

**[SUPERSEDIDO por la prueba del 2026-11-10]** La URL `data_EDS.js` responde con un tipo de contenido JavaScript (`application/x-javascript`) según el lector web, que no puede abrirlo como documento de texto soportado. Desde el entorno de creación de este archivo también falló la consulta directa por resolución DNS; **no** se obtuvo el cuerpo actual, código HTTP verificable ni muestra completa reciente. Por ello quedan pendientes el esquema, el payload actual y la prueba end-to-end. La incapacidad de leerlo desde estas herramientas **no demuestra** que el sitio esté caído para usuarios o para OpenCode local.

**[VERIFICADO: 2026-11-10, prueba en vivo]** El recurso se obtuvo con `HTTP 200` desde el host y desde el contenedor del backend: `Content-Type: application/x-javascript`, `Server: Lotus-Domino`, ~1,35 KB, UTF-8, CRLF y un `Last-Modified` que avanzó entre consultas (~5–6 min). El cuerpo es un literal de datos `var data = { … }` (claves sin comillas, comillas simples), **no JSON válido**. Con los ajustes TLS por defecto de OpenSSL la consulta falla con `SSLV3_ALERT_HANDSHAKE_FAILURE`; funciona con `set_ciphers("DEFAULT@SECLEVEL=1")` conservando la verificación de certificado y hostname. El esquema observado, los límites geográficos y el contrato propuesto se registran en la sección 8 y en `openspec/changes/archive/2026-11-10-implement-current-outages-cu01/`.

**[ANTECEDENTE: código público de 2020]** Una integración de terceros obtiene el recurso mediante `requests.get(...)`, remueve el prefijo `var data = ` y decodifica el objeto resultante con un parser tolerante. Utiliza una colección denominada `cortesServicioBaja` y los campos `partido` y `localidad`. Estos nombres son **evidencia histórica**, no esquema actual confirmado. Referencia: https://gist.github.com/fabio195/91fc7593f3d537f61c4875116931f37b

## 2. Cómo consultar el recurso

### 2.1. HTTP de lectura

- **Método:** `GET`.
- **Path:** `/paginacorte/js/data_EDS.js`.
- **Host:** `www.enre.gov.ar`.
- **Autenticación conocida:** el recurso fue usado públicamente sin clave en integraciones previas; **confirmar en la prueba actual**.
- **Body:** ninguno.
- **Parámetros requeridos conocidos:** ninguno. El sufijo `?` que aparece en algún código antiguo no acredita un parámetro de API.
- **Headers recomendados:** `Accept: application/javascript, text/javascript, */*`, `User-Agent: EnergiaSur/1.0 (proyecto educativo)`; no son headers exigidos oficialmente.
- **Timeout y reintentos:** se definen en Energía Sur, no están documentados por ENRE; proponer timeout acotado y reintentos limitados con backoff para errores transitorios.
- **TLS:** verificar certificados; no usar `verify=False` o `-k` como solución de producción.
- **Cache-Control / ETag / Last-Modified:** registrar si existen; no asumirlos.
- **CORS:** no depende del navegador si la llamada se hace desde FastAPI. **No acceder directamente desde React.**

#### PowerShell: prueba manual, solo lectura

```powershell
$uri = 'https://www.enre.gov.ar/paginacorte/js/data_EDS.js'
$response = Invoke-WebRequest -Uri $uri -Method Get -TimeoutSec 20 -Headers @{
  'Accept' = 'application/javascript, text/javascript, */*'
  'User-Agent' = 'EnergiaSur-CU01-Research/1.0'
}
$response.StatusCode
$response.Headers['Content-Type']
$response.Content.Substring(0, [Math]::Min(600, $response.Content.Length))
```

**Precaución:** imprimir solo una muestra acotada; no copiar contenido remoto sin inspeccionarlo ni ejecutarlo. PowerShell 5.1 puede requerir `-UseBasicParsing`; PowerShell 7 no.

#### curl: inspección de headers y texto

```bash
curl -L --max-time 20 -D - -o /dev/null 'https://www.enre.gov.ar/paginacorte/js/data_EDS.js'
curl -L --max-time 20 'https://www.enre.gov.ar/paginacorte/js/data_EDS.js' | head -c 600
```

El segundo comando inspecciona una muestra y puede producir aviso de tubería cerrada por `head`; no constituye un fallo de la fuente. No lanzar peticiones repetidas sin control.

### 2.2. Formato bruto esperado: evidencia versus hipótesis

**[ANTECEDENTE]** El recurso **podría** tener forma general:

```javascript
var data = { /* propiedades del ENRE aún no confirmadas en la versión actual */ };
```

**Esto es un ESQUEMA ILUSTRATIVO, NO un payload capturado en 2026.**

**[ANTECEDENTE]** `cortesServicioBaja` es un nombre utilizado por código público antiguo; existen referencias históricas a `partido` y `localidad`.

**[PENDIENTE]** Comprobar:

- Prefijo real (`var data =`, otro nombre, asignación, JSON literal, etc.) y posibles instrucciones adicionales.
- Si el contenido entre la asignación y el terminador es JSON válido o un objeto literal de JavaScript (claves sin comillas, comentarios, comillas simples, `undefined`, etc.).
- Nombres y tipos exactos de las claves raíz, colecciones y totales.
- Si la información pertenece solo a Edesur, incluye otras distribuidoras o necesita selección interna.
- Campo(s) de fecha/hora, zona horaria y semántica de actualización.
- Tipos de interrupción realmente presentes, categorías vacías y valores nulos.
- Codificación de respuesta (UTF-8, ISO-8859-1 u otra) y normalización de tildes.
- Estabilidad del orden, duplicados y posibles identificadores.
- Cambios de estructura entre consultas sucesivas.

### 2.3. Estrategia segura de parsing

**[PROPUESTA]** Hacer parsing estricto, **no ejecutar JavaScript**:

1. Descargar el recurso con `httpx` u otro cliente ya existente (verificar dependencias del proyecto).
2. Limitar tamaño del body y tiempo de lectura.
3. Detectar la forma exacta de asignación **solo después de observar la respuesta**.
4. Extraer únicamente el literal de datos, rechazando código adicional no permitido.
5. Si el literal es JSON compatible, usar `json.loads`; de lo contrario, evaluar **un parser de JavaScript seguro orientado a datos** y justificarlo, sin `eval`, `exec`, Node VM ni ejecución de scripts remotos.
6. Validar la estructura con esquemas tipados, valores numéricos no negativos, límites y tipos esperados.
7. Separar `raw -> parse -> normalize -> validate -> persist`, conservando errores diagnósticos sin exponer contenido potencialmente hostil.
8. Ante esquema desconocido o parseo fallido, **mantener el último snapshot válido**, marcar la falla y nunca sustituirlo por lista vacía.

No adoptar un parser genérico o una librería nueva antes de inspeccionar una captura auténtica.

## 3. Categorías que muestra la página oficial

**[VERIFICADO: interfaz web del ENRE, no confirmación del esquema JS]** La página `tabla_cortes_edesur.html` contiene las siguientes categorías:

| Categoría visible | Campos presentados en la tabla | Consideración |
|---|---|---|
| Cortes preventivos | Partido, localidad/barrio, subestación/alimentador, usuarios afectados, hora estimada de normalización | Determinar si se incluyen en «cortes actuales». |
| Cortes programados por mantenimiento y obras | Los mismos campos | Separar de trabajos futuros de CU02; no duplicar responsabilidades. |
| Interrupciones de media tensión | Partido, localidad/barrio, subestación/alimentador, usuarios afectados, hora estimada de normalización | Candidatas para CU01. |
| Cortes programados por comunicado | Hora programada, partido, localidad, subestación/alimentador, usuarios, normalización, zona afectada/calles | Validar temporalidad y pertenencia a CU01 o CU02. |
| Interrupciones de baja tensión | Partido, localidad/barrio, usuarios afectados | La tabla **no ofrece** normalización ni subestación para esta categoría. |

También presenta totales de usuarios con/sin suministro, «última actualización» y afectados del día anterior. **No inferir que todos estos elementos existen como campos del JS ni que una lista sin filas significa falla.**

Fuente: https://www.enre.gov.ar/paginacorte/tabla_cortes_edesur.html

## 4. Cobertura territorial y geolocalización

**[VERIFICADO]** Las tablas oficiales exponen **partido** y **localidad/barrio**. Ciertos cortes muestran subestación/alimentador o zona afectada/calles.

**[PENDIENTE]** El recurso `data_EDS.js` podría contener campos adicionales, pero **no se verificaron coordenadas, polígonos de afectación, códigos GeoRef, direcciones exactas ni relación medidor-alimentador**.

**[PROPUESTA]** Para el primer diseño de CU01:

- Filtro territorial principal por `partido` y `localidad`, conservando los nombres originales y una clave normalizada para comparación.
- Para **dirección**, resolver mediante GeoRef o componentes existentes hasta partido/localidad; advertir que se trata de coincidencia **por zona**, no por domicilio exacto.
- Para **geolocalización del dispositivo**, convertir lat/lon en división territorial mediante un servicio de geocodificación inversa autorizado/ya disponible. No calcular radios de afectación con coordenadas inventadas.
- Ante localidades homónimas, usar partido + localidad; ante zona no identificada, pedir seleccionar localidad sin declarar que no hay cortes.
- Confirmar cobertura geográfica real de Edesur antes de suponer que cualquier localidad del AMBA está cubierta.

## 5. Contrato interno propuesto para Energía Sur (NO es el contrato del ENRE)

**[PROPUESTA]** Estos nombres son sugerencias de diseño y deben revisarse contra OpenSpec, `AGENTS.md` y convenciones actuales antes de aprobarlos.

Ejemplo conceptual de respuesta de **nuestra API** (datos ficticios, no un corte real):

```json
{
  "source": "ENRE",
  "distributor": "EDESUR",
  "source_url": "https://www.enre.gov.ar/paginacorte/js/data_EDS.js",
  "fetched_at": "2026-11-10T12:05:00Z",
  "source_updated_at": null,
  "freshness": "fresh",
  "coverage": { "partido": "LOMAS DE ZAMORA", "localidad": "BANFIELD" },
  "outages": [
    {
      "category": "medium_voltage",
      "partido": "LOMAS DE ZAMORA",
      "localidad": "BANFIELD",
      "affected_users": 20,
      "substation_or_feeder": null,
      "estimated_restoration_at": null,
      "geometry": null
    }
  ]
}
```

Notas:

- El ejemplo **no representa datos observados**; ninguna cifra, zona o fecha debe tomarse como real.
- `fetched_at` es la fecha UTC en que **nuestro servidor** obtuvo una respuesta válida, no la publicación ENRE.
- `source_updated_at` solo se completará si la fuente comunica una fecha interpretable y verificable.
- `freshness` es una clasificación de Energía Sur (`fresh`, `stale`, `unavailable` u otra acordada); las ventanas temporales deben definirse explícitamente.
- `outages: []` solo comunica ausencia de registros en la cobertura solicitada **cuando existe un snapshot válido y suficientemente reciente**.
- Las coordenadas, IDs, fechas de inicio y duración serán nulos/omitidos salvo que la fuente realmente los proporcione.
- Evitar confundir totales por región con cantidad total de registros y evitar sumar agregaciones superpuestas.

## 6. Actualización, persistencia y manejo de fallos

**[PROPUESTA SUJETA A PLAN]**

- Realizar la consulta **server-to-server** desde el backend; React solo consulta la API propia.
- Usar **intervalo inicial sugerido de 5 minutos**, alineado con la periodicidad declarada del ENRE; parametrizable y sin garantizar que el dato cambie en cada consulta.
- Guardar el **último snapshot válido** y metadatos mínimos: fecha/hora UTC de fetch, timestamp de origen si existe, hash del contenido/versión de esquema, cantidad de registros, estado y error de la última ejecución.
- No borrar el snapshot válido al fallar una actualización. Diferenciar `no_reported_outages`, `source_stale`, `source_unavailable`, `unsupported_area` y `parse_error` (nombres internos a consensuar).
- Fijar política de frescura, reintentos limitados, límites de concurrencia y prevención de polls simultáneos; verificar la topología Docker/multiproceso existente antes de elegir scheduler.
- Definir si cada actualización reemplaza el estado actual o se guardan snapshots históricos. CU01 necesita un **estado vigente**; no inferir eventos continuos ni inicio/fin de cortes a partir de snapshots sin reglas adicionales.
- Diseñar un punto de extensión sencillo para CU10, **sin implementar** el panel administrativo ni controles de periodicidad de CU10 en CU01.
- Respetar restricciones del recurso y no utilizar el HTML como scraping masivo.

## 7. Pruebas y criterios mínimos de aceptación para pasar de investigación a PROPOSE

**Pruebas de investigación (sin modificar repositorio):**

1. Capturar status code, headers relevantes, fecha de consulta y muestra **redactada/limitada** del cuerpo real.
2. Verificar que el recurso sea accesible desde el entorno local donde corre el backend (preferentemente también desde Docker si está disponible).
3. Obtener al menos una muestra auténtica y documentar nombres de claves, tipos, listas vacías y anomalías.
4. Identificar categorías actuales y sus campos con evidencia, y contrastarlas contra la tabla oficial.
5. Identificar presencia o ausencia de timestamps, coordenadas y IDs.
6. Consultar una segunda vez con intervalo razonable para comparar semántica de actualización y headers, sin generar tráfico excesivo.
7. Evaluar un parser que **no ejecute JS**; plantear fixtures basados en datos redactados obtenidos realmente y fixtures artificiales **claramente rotulados** para casos borde.
8. Inspeccionar la arquitectura actual antes de proponer nuevos servicios, tablas, schedulers o dependencias.
9. Verificar tratamiento de respuesta inválida, fuente caída, contenido viejo, duplicados, cambios de esquema y zona sin datos.
10. Entregar un inventario de decisiones pendientes; **no empezar PROPOSE** sin aprobación humana.

**No alcanza para aprobar:** que `GET` retorne algo, que el HTML oficial tenga tablas o que una implementación de terceros use un esquema en 2020.

## 8. Decisiones explícitas y pendientes

| Tema | Estado |
|---|---|
| ENRE como fuente primaria de CU01 | **Aprobado por el usuario**; recurso validado en vivo el 2026-11-10 |
| URL primaria `data_EDS.js` | **Validada en vivo**: HTTP 200, literal JS de datos, UTF-8, `Last-Modified` activo |
| Integración backend->ENRE->API propia | **Aprobada para CU01 (D1/D5/D6)**; sin implementar |
| Frecuencia de consulta cada 5 minutos | **Aprobada para CU01 (D6)**; operación final configurable |
| Formato JS y claves | **Verificado**: claves raíz y filas de programados/baja; media/preventivo y comunicados no observados |
| Contrato normalizado | **Definido en** `openspec/changes/archive/2026-11-10-implement-current-outages-cu01/` |
| Geocodificación / filtros por dirección o GPS | **Aprobada para CU01 (D2/D9/T1)** con GeoRef en backend y degradación a partido; mapeo de nombres y catálogo de cobertura pendientes |
| Umbral de información desactualizada | **Aprobado para CU01 (D8)**: fresh ≤15 min, stale ≤60 min, unavailable >60 min |
| Persistencia y orquestador | **Aprobados para CU01 (D5/D6)**: PostgreSQL + advisory lock; sin implementar |
| Uso de fuentes alternativas (Edesur directo, ¿Hay luz?) | **No autorizado para cambiar la fuente primaria**; requieren decisión humana |
| Autenticación de consulta CU01 | Propuesta original: **consulta disponible a visitantes** |

## 9. Trazabilidad y enlaces

### Fuentes oficiales

1. ENRE, tabla de cortes Edesur: https://www.enre.gov.ar/paginacorte/tabla_cortes_edesur.html
2. ENRE, recurso bruto: https://www.enre.gov.ar/paginacorte/js/data_EDS.js
3. Gobierno argentino, estado del servicio Edesur: https://www.argentina.gob.ar/enre/estado-del-servicio-electrico-de-edesur
4. ENRE, mapa de cortes: https://www.enre.gov.ar/mapacortes/index.html

### Fuentes complementarias (no contractuales)

5. Ejemplo histórico de cliente Python que consulta `data_EDS.js`: https://gist.github.com/fabio195/91fc7593f3d537f61c4875116931f37b
6. Explicación de metodología de un consumidor no oficial del ENRE: https://cortesdeluz.com.ar/metodologia/
7. Documentación del agregador independiente (no usar como fuente sin autorización): https://cortesdeluz.com.ar/datos/

### Base documental del TP

- Propuesta aprobada para Energía Sur: CU01 contempla cortes por dirección, ubicación o localidad; consulta pública, fuente y fecha de actualización.
- CU02 está separado para trabajos programados próximos.
- CU10 contempla supervisión de obtención automática de fuentes.
- Las decisiones de detalle deben contrastarse con la documentación actual del repositorio.

---

**Instrucción final para OpenCode:** usar este documento como contrato verificado de la fuente y lista de verificación. **No codificar contra un supuesto no observado:** el payload `data_EDS.js` fue validado en vivo el 2026-11-10. CU01 fue sincronizado y archivado el 2026-11-10; las excepciones 0.1 (formas pobladas de media/preventivo no observadas) y 0.4 (catálogo parcial de nueve localidades) quedaron aceptadas en U20. No ampliar cobertura ni afirmar categorías pobladas verificadas sin evidencia nueva.
