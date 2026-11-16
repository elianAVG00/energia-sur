# Documentación de Energía Sur

El [README principal](../README.md) presenta el proyecto y explica cómo iniciar la
aplicación completa. Este índice reúne especificaciones, decisiones, guías y
bitácoras para profundizar sin sobrecargar esa entrada.

## Requisitos, arquitectura y estado

| Documento | Contenido y alcance |
| --- | --- |
| [Estado operativo](STATE.md) | Últimos resultados, cambios activos, bloqueos y siguientes acciones. |
| [Catálogo de diez casos de uso](use-cases/README.md) | Fichas de la propuesta y base documental aceptada de la etapa 05. Sus estados iniciales no son un inventario actualizado de implementación. |
| [Reglas compartidas](use-cases/shared-rules.md) | Reglas transversales de la base documental. |
| [Decisiones y aprobaciones](use-cases/decisions.md) | Confirmaciones humanas, revisiones posteriores y preguntas abiertas. |
| [Especificaciones OpenSpec](../openspec/specs/) | Requisitos y escenarios por capacidad. Contrastar con los deltas de cambios activos y sus aprobaciones. |
| [Cambios OpenSpec](../openspec/changes/) | Propuestas, diseños, contratos y tareas activos; `archive/` conserva los entregados. |
| [Diseño inicial de persistencia, sesiones y PDF](../openspec/changes/archive/2026-11-08-record-cu09-interruption-diary/design.md) | Decisiones arquitectónicas de CU09, complementadas por los diseños de cada cambio posterior. |
| [Contexto de la etapa 05](stage-05-context.md) | Síntesis de fuentes académicas y límite autorizado de esa etapa. |
| [Workflow OpenSpec](openspec-workflow.md) | Mecanismos instalados y proceso Explore → Propose → Review → Apply → Verify → Archive. Incluye instantáneas históricas de la etapa 05. |
| [Base compartida del frontend](frontend-foundation.md) | Módulos, sesión, formularios, transporte y reutilización. |
| [Guía operativa y contrato del backend](../backend/README.md) | Cuentas, almacenamiento privado, ingesta, ejecutores y verificaciones locales detalladas. |
| [Integración ENRE](integrations/ENRE_CU01_INTEGRACION_FUENTE.md) | Investigación y contrato de fuente observado para CU01. |
| [Guía de Edesur](../backend/knowledge/guia-oficial-edesur.md) | Base documental del asistente con fuentes, procedencia y fechas de verificación. |

OpenSpec describe el comportamiento esperado; código y pruebas aportan evidencia
de implementación. Una tarea marcada o una validación estructural no acredita por
sí sola aceptación funcional. Las bitácoras conservan sus etapas y resultados con
fecha: un bloqueo antiguo puede tener resolución posterior en el mismo registro.

## AI Engineering: índice completo de bitácoras

Cada registro conserva objetivo, artefactos, decisiones, herramientas, intervenciones,
problemas, correcciones, resultados y limitaciones. Los enlaces de cada bitácora
permiten llegar a los cambios OpenSpec y a las evidencias originales.

| Bitácora | Para qué consultarla |
| --- | --- |
| [Catálogo y SDD, etapa 05](ai-engineering/stage-05-sdd.md) | Prompts de contraste, fuentes, validación documental/estructural y aceptación U06. |
| [Entorno Docker](ai-engineering/docker-development-environment.md) | Decisiones, imágenes, comprobaciones de proxy/persistencia y tareas históricas de cierre abiertas. |
| [MCP de desarrollo](ai-engineering/configure-readonly-development-mcp.md) | GitHub/Context7, permisos, autenticación, descubrimiento y llamadas reales redactadas. |
| [CU09: diario de interrupciones](ai-engineering/record-cu09-interruption-diary.md) | Contrato inicial, sesiones, Origin/CSRF, fechas, PDF y aceptación con datos sintéticos. |
| [Base compartida del frontend](ai-engineering/establish-frontend-foundation.md) | Adopción de formularios, componentes, estado y transporte; evidencia de revisión. |
| [CU04: domicilios y medidores](ai-engineering/manage-cu04-domiciles-meters.md) | Propiedad, concurrencia, pruebas y corrección de pérdida de borradores. |
| [CU05: lecturas y OCR](ai-engineering/record-cu05-meter-readings.md) | Fotos privadas, OCR acotado, resolución del contrato de fracciones rojas y límites aceptados. |
| [CU06: facturas](ai-engineering/record-cu06-electricity-bills.md) | Contratos, PDF, adjuntos privados, reconciliación y ensayo coordinado de respaldo/restauración. |
| [CU07: comparación de consumos](ai-engineering/compare-cu07-consumption-with-bill.md) | Selección y confirmación de períodos, cálculo exacto y verificaciones. |
| [CU08: evolución y estimaciones](ai-engineering/view-cu08-consumption-evolution-and-estimates.md) | Fórmulas, intervalos, presentación orientativa y pruebas. |
| [CU01: cortes actuales](ai-engineering/implement-current-outages-cu01.md) | ENRE, GeoRef, contrato público, interfaz y comprobaciones reales/con mocks por BUILD. |
| [CU02: trabajos informados por ENRE](ai-engineering/implement-scheduled-works-cu02.md) | Alcance U22, trazabilidad de la propuesta original y límites de la fuente. |
| [CU03: asistente integrado](ai-engineering/implement-integrated-assistant-cu03.md) | RAG, herramientas internas, memoria, SSE, revisión y consulta real de OpenAI. |
| [CU10: supervisión de fuentes](ai-engineering/supervise-source-refresh-cu10.md) | Roles, reintentos, bloqueos, intervalos persistidos y aceptación pendiente en navegador real; [cambio archivado](../openspec/changes/archive/2026-11-13-supervise-source-refresh-cu10/proposal.md). |
| [Estabilización de pruebas CU05/CU06](ai-engineering/stabilize-cu05-cu06-backend-test-runtime.md) | Problemas del entorno, ejecutor focalizado y resultados históricos por suite. |
| [Aislamiento del historial CU05](ai-engineering/isolate-cu05-reading-history-by-meter.md) | Reproducción, causa, evidencia rojo/verde, revisión y QA-INT-CU04-08 diferido. |
| [Retiro del panel de salud público](ai-engineering/remove-public-api-health-panel.md) | Decisión U26, reconciliación del contrato y comprobación HTTP; [cambio archivado](../openspec/changes/archive/2026-11-14-remove-public-api-health-panel/proposal.md). |
| [Identidad visual y consulta CU01](ai-engineering/redesign-public-shell-cu01.md) | Navegación, paleta, componentes, capturas y resultados por etapa. |
| [Rediseño de trabajos y administración](ai-engineering/redesign-public-works-admin.md) | Presentación CU02/CU10, revisión, capturas y límites preservados; [cambio archivado](../openspec/changes/archive/2026-11-14-redesign-public-works-admin/proposal.md). |
| [Rediseño de Mi cuenta](ai-engineering/redesign-account-workspace.md) | Etapas 0/A–E, contexto de trabajo, capturas, regresión PDF y revisión acumulada; [cambio archivado](../openspec/changes/archive/2026-11-15-redesign-account-workspace/proposal.md). |
| [Catálogo territorial compartido](ai-engineering/unify-territorial-catalog.md) | Cambio activo: procedencia GeoRef, alias, migraciones, paridad API y revisión pendiente. |
| [Registro público de cuentas](ai-engineering/add-public-account-registration.md) | Cambio activo: aceptación integral específica aprobada; suite backend amplia FAIL (476/8/7) por ocho fallos CU01/CU02 ajenos al registro. |

No hay un documento único dedicado a seguridad o testing: las pruebas y los
controles están registrados por cambio, en sus contratos y bitácoras. La
[Skill quality-gate](../.agents/skills/quality-gate/SKILL.md) define el procedimiento
para seleccionar controles, registrar evidencia y distinguir PASS, FAIL, BLOCKED y
NOT APPLICABLE. La [Skill fastapi-endpoint](../.agents/skills/fastapi-endpoint/SKILL.md)
guía cambios de endpoints bajo un contrato aceptado.

## Reorganización del README — 16/11/2026

La referencia de presentación fue el [README de Donata IA](https://github.com/Gonzacerbelli/donata-ia/blob/main/README.md),
consultado mediante el conector GitHub MCP de lectura de Codex. La respuesta
identificó el archivo con SHA `e3db6e7455c980a96473724395d9924336d708ce`.
Se adoptaron la secuencia de diez secciones, las tablas y la separación entre
presentación y detalle. Donata utiliza un esquema textual de arquitectura;
Energía Sur incorpora un diagrama Mermaid por pedido del usuario. No se
trasladaron tecnologías ni capacidades del proyecto de referencia.

Este cambio es exclusivamente documental y no requiere una nueva propuesta
OpenSpec: reorganiza explicaciones de contratos existentes. El usuario autorizó
expresamente el README en español, lo que prima para este trabajo sobre las
instrucciones previas de redactar documentación en inglés. No se modifica esa
configuración ni se resuelven decisiones funcionales o técnicas.

| Contenido del README anterior | Destino de consulta |
| --- | --- |
| Inicio parcial de infraestructura y conexión CU09 en apartados separados | Secuencia única de aplicación completa en el README; aclaraciones de conexión en la guía del backend. |
| Comandos CLI, almacenamiento, reinicios e ingesta del asistente | [Operación local del backend](../backend/README.md#operación-local-y-verificaciones). |
| Ejecutor CU09, ejecutor focalizado CU05/CU06 y pruebas de infraestructura/fuentes | Misma guía; se preservan efectos sobre recursos, requisitos y límites. |
| Contratos y validaciones particulares de cada CU | Especificaciones vigentes, fichas y bitácoras ya existentes, enlazadas en este índice. |
| Paleta, componentes y etapas de rediseño | Guía del frontend y bitácoras visuales; el README resume responsabilidades y estado. |
| Configuración y autenticación MCP | Bitácora MCP original; el README conserva un resumen y la distinción respecto del chatbot. |
| Listado disperso de evidencias y cambios | Índice completo de bitácoras de este documento, incluidos los dos cambios funcionales activos y las entregas archivadas. |

Al contrastar las fuentes se conservaron estas diferencias explícitas:

- El catálogo de CU y parte del workflow conservan estados de la etapa 05 que no
  reflejan la implementación posterior. Consultar STATE, especificaciones y los
  últimos checkpoints de las bitácoras para conocer el estado actual.
- El README anterior describía Mi cuenta hasta la etapa C como no archivado; la
  bitácora del 15/11 y STATE registran el cierre acumulado de las etapas 0/A–E.
- `AGENTS.md` enumera decisiones originalmente pendientes que luego se aprobaron
  por cambio; los diseños y el registro de decisiones documentan esas resoluciones.
  No se alteró AGENTS ni se adoptaron decisiones nuevas.
- Las variables de intervalo `*_REFRESH_SECONDS` permanecen en Compose, pero los
  intervalos efectivos se leen de la configuración persistida de CU10.
- En la reorganización inicial del README no estaba disponible el reporte del registro:
  se habían informado 15 fallos y la aceptación integral no se había ejecutado. El
  seguimiento posterior generó un reporte nuevo (491: 476 PASS, 8 FAIL, 7 SKIP) y
  completó la aceptación sintética específica; los ocho fallos CU01/CU02 y los
  bloqueos de QA-INT-CU04-08 se mantienen separados y documentados.
- La redefinición CU02 está autorizada por U22, sin evidencia de aprobación docente
  de ese cambio de alcance. El borrado automático de memoria a los 30 días tampoco
  se presenta como implementado.

La revisión documental usa la Skill `quality-gate`; no ejecuta pruebas de la
aplicación, migraciones ni llamadas a OpenAI. No incluye commit, push o archive,
ni modifica STATE, OpenSpec, agentes, Skills, MCP, dependencias o código fuente.

### Verificación documental realizada

Controles ejecutados por Codex el 16/11/2026 desde la raíz del repositorio.
Se usaron Node 24.11.1, el parser Marked 18.0.9 ya instalado con una extensión de
VS Code, el parser Mermaid incluido en VS Code y Docker Compose v2.40.3-desktop.1.
No se instalaron herramientas ni se cambiaron dependencias.

| Control | Resultado y evidencia |
| --- | --- |
| Estructura del README | PASS: 303 líneas, título solicitado, diez secciones numeradas y una fila por CU01–CU10. |
| Markdown y referencias | PASS: parsing GFM de los cuatro documentos; enlaces locales y anclas comprobados, tablas con columnas consistentes y bloques de código cerrados. |
| Diagrama Mermaid | PASS sintáctico: gramática real de flowchart, nueve nodos y nueve aristas; un control mal formado fue rechazado. Se adaptó únicamente la sanitización de etiquetas de texto plano para ejecutar el parser sin DOM. No se inspeccionó el render en GitHub. |
| PowerShell | PASS: los 16 bloques de comandos pasaron el parser de PowerShell sin ejecutar su contenido. |
| Docker Compose | PASS: `docker compose --env-file <archivo-temporal-sintetico> -f compose.yaml -f compose.cu09.yaml config --quiet`, salida 0; sin leer el `.env` local ni iniciar servicios. La ayuda instalada confirma las opciones de inicio utilizadas. |
| Tecnologías y herramientas | PASS documental: scripts npm contrastados con el manifiesto; dependencias Python, cinco agentes, ocho Skills, seis comandos y dos definiciones MCP comprobados en archivos. No implica una invocación nueva de todos esos recursos. |
| Conservación | PASS: los 46 destinos de archivos enlazados en el README anterior siguen referenciados desde la nueva entrada, el índice, las guías o las bitácoras; las 22 bitácoras Markdown están indexadas. Revisión manual de la correspondencia de contenido trasladado. |
| Diff y alcance propio | PASS: `git diff --check` de los cuatro Markdown y `git diff --cached --check`; escrituras limitadas a esos documentos. Comparación con hashes iniciales y revisión del diff, con la salvedad concurrente indicada abajo. |
| Suite de aplicación y aceptación en ejecución | NOT APPLICABLE para este cambio documental, por instrucción expresa. No se ejecutaron tests, builds, migraciones ni verificaciones con OpenAI. |
| Validación estructural OpenSpec | NOT APPLICABLE: no se modificaron artefactos OpenSpec ni su configuración. |

La revisión es documental y propia, no una revisión funcional independiente. El
árbol ya contenía cambios al inicio. Durante la tarea también cambiaron los hashes
de `frontend/e2e/public-registration.spec.ts` y `scripts/Test-Cu09Acceptance.ps1`
por trabajo concurrente; Codex no los editó ni revirtió. No se atribuye a esta
refactorización el diff previo o concurrente de esos archivos.
