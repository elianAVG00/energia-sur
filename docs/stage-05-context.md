# Energía Sur · Contexto para la etapa 05 — SDD con OpenSpec

Este archivo resume las fuentes del TP y define el alcance de la etapa 05. La síntesis de los PDF permite trabajar con este Markdown y el checkout. Las fichas que produzca esta etapa describen comportamiento planificado para revisión.

## Fuentes y estado de referencia

- **Propuesta del TP** — `Elian Gonzalez- Grupo 18 - Propuesta de TP Integrador (1).pdf`, pp. 1–2. Define el producto y los diez CU del catálogo de abajo.
- **Consigna docente** — `Lineamientos TP.pdf`, pp. 1–2. Define la evaluación y el visto bueno previo a programar el TP.
- **Checklist del proyecto** — La etapa 05 configura OpenSpec y documenta los diez CU. La etapa 06 elige y desarrolla el primer CU supervisado. La etapa 07 reúne evidencia, quality gates y verificación de entrega.
- **Checkout** — `AGENTS.md` rige el trabajo. `docs/STATE.md`, `README.md` y los artefactos de OpenSpec aportan el estado y la evidencia. Verificá su contenido local. Priorizá las decisiones explícitas del usuario y la evidencia más reciente sobre recomendaciones previas. `Grupo 18.pdf` es un ejemplo de inventario de ferretería.

## Producto y requisitos docentes

Energía Sur es una aplicación web para vecinos de Zona Sur que usan Edesur. Las consultas de cortes, los trabajos programados y el chat son públicos. Con cuenta se pueden guardar domicilios, medidores, lecturas con fotos, facturas y un diario de interrupciones. La propuesta prevé actualización automática desde ENRE y Edesur, fecha de actualización visible, GeoRef como ayuda para ubicar direcciones y fuentes oficiales para el chat. El usuario aporta sus registros personales.

El TP pide una aplicación web con frontend y backend, diez CU propuestos antes del desarrollo, al menos siete resueltos de forma interactiva y sin errores críticos, un chat integrado con un framework de IA como LangChain y al menos dos herramientas o servidores MCP en desarrollo o en la arquitectura, con al menos un servidor externo. Se evalúa la orquestación con agentes y la gestión de contexto. El README de entrega debe explicar la arquitectura y los CU, documentar prompts, metodología, ciclos de autocorrección si los hubo, instrucciones y configuración y rol de los MCP.

Verificá si hay evidencia del **visto bueno docente sobre el tema y los diez CU**. En el último estado contrastado seguía sin documentarse. Es un requisito previo a implementar funcionalidad. La etapa 05 puede avanzar como documentación. CU09 es candidato para la etapa 06, sujeto a revisión y a sus dependencias.

## Decisiones del proyecto y último estado observado

- Repo `elianAVG00/energia-sur`. Proyecto individual, trabajo directo en `main`, Conventional Commits, Windows con PowerShell. OpenCode implementa y Codex audita de forma independiente. Esta ejecución no autoriza commit ni push.
- Stack decidido: React + TypeScript con Vite y npm, Python + FastAPI con Uvicorn y `uv`, PostgreSQL en Docker Compose. El asistente integrado usará LangChain y la API de OpenAI en el backend. Driver, ORM, migraciones y conexión FastAPI–PostgreSQL quedaron fuera de Docker. Buscá evidencia de decisiones posteriores antes de darlas por aprobadas.
- En el `main` consultado, el Verify focalizado de `docker-development-environment` documentaba **18/22 tareas evidenciadas**, los tres servicios saludables, persistencia PostgreSQL y aceptación humana en navegador de éxito, error y recuperación. El cambio seguía abierto. Las tareas 1.4, 2.4, 7.1 y 7.2 quedaban pendientes por lint y tipado estático del backend. Confirmá cualquier avance posterior con las tareas y la evidencia en `docs/ai-engineering/`.
- GitHub MCP de lectura y Context7 tienen llamadas de verificación registradas en `configure-readonly-development-mcp`. Son herramientas de desarrollo. Preservá su configuración y permisos. OpenSpec se observó con CLI 1.16.1, schema `spec-driven` y artefactos en inglés. Confirmá las convenciones, la versión y el perfil instalados.

## Catálogo funcional de referencia

| ID | Caso de uso | Actor | Alcance de la propuesta |
| --- | --- | --- | --- |
| CU01 | Consultar cortes actuales en una zona | Visitante o vecino con cuenta | Consulta cortes informados por dirección, ubicación del dispositivo o localidad. Muestra fuente y fecha de actualización. |
| CU02 | Consultar trabajos programados próximos | Visitante o vecino con cuenta | Filtra por zona y fechas. Consulta inicio, fin, motivo y cercanía. |
| CU03 | Obtener orientación con el asistente integrado | Visitante o vecino con cuenta | Conversa sobre cortes, trabajos y procedimientos de consulta o reclamo. Las respuestas usan guías oficiales y datos públicos actualizados e indican sus fuentes. |
| CU04 | Gestionar domicilios y medidores personales | Vecino con cuenta | Guarda y modifica domicilios y medidores para asociarlos a consultas, lecturas, facturas e interrupciones. |
| CU05 | Registrar una lectura del medidor con foto | Vecino con cuenta | Registra fecha y lectura acumulada en kWh, adjunta una foto y confirma el valor antes de incorporarlo al historial. |
| CU06 | Registrar una factura eléctrica | Vecino con cuenta | Guarda período, kWh facturados y archivo de factura vinculados al domicilio y medidor. El importe es opcional. |
| CU07 | Contrastar el consumo registrado con la factura | Vecino con cuenta | Compara la diferencia entre lecturas del mismo medidor con los kWh facturados para un período compatible y consulta las diferencias. |
| CU08 | Consultar evolución y estimación del consumo | Vecino con cuenta | Consulta consumos y promedios diarios. Con al menos dos lecturas válidas obtiene una estimación en kWh para un período elegido. |
| CU09 | Registrar y consultar un diario de interrupciones | Vecino con cuenta | Registra inicio, fin, observaciones y número de reclamo opcional. Admite cortes en curso, filtro por período y descarga de un PDF con los registros y las horas sin servicio para acompañar un reclamo. |
| CU10 | Supervisar la actualización automática de fuentes | Administrador | Consulta últimas actualizaciones y errores, reintenta la obtención y ajusta intervalos de fuentes habilitadas. La carga de datos públicos es automática. |

## Entregables de la etapa 05

1. **Inspección y contraste.** Desde la raíz, verificá rama, HEAD y cambios locales. Leé `AGENTS.md`, las reglas aplicables, `docs/STATE.md`, README, `openspec/config.yaml` y los changes pertinentes. Conservá los cambios ajenos y cargá solo contexto relevante. Usá `spec-analyst` en modo de solo lectura para contrastar este catálogo con el checkout, detectar contradicciones y listar preguntas por CU. Si el agente no está disponible, registrá cómo se hizo el contraste.
2. **Configuración.** Actualizá `openspec/config.yaml` con las convenciones verificadas y campos soportados. Documentá **Explore → Propose → Review → Apply → Verify → Archive** y distinguí comandos o skills realmente instalados de pasos del equipo. Review es la aprobación humana explícita antes de Apply. Verify exige evidencia y Archive queda sujeto a los controles y la autorización aplicables.
3. **Catálogo.** Reutilizá la estructura e idioma del repo. Creá o completá un índice bajo `docs/` con una ficha independiente por ID. Incluí fuente, estado, actor, precondiciones, flujo principal, alternativas, reglas, dependencias y escenarios verificables Dado/Cuando/Entonces. Vinculá cada escenario con su regla o fuente y documentá una sola vez las reglas compartidas. Reservá `openspec/specs/` para comportamiento vigente. Cada CU pasará a un change cuando se autorice proponer su implementación.
4. **Trazabilidad.** Separá alcance de la propuesta, decisiones confirmadas, inferencias y TBD. Registrá la pregunta concreta, su motivo y qué CU o escenario bloquea. Para CU09, verificá permisos por domicilio, intervalos superpuestos y cómputo de horas cuando un corte cruza un límite del período. Si no hay evidencia de aprobación, dejá cada regla como TBD. Hacé lo mismo para la compatibilidad de períodos de CU07 y el método de estimación de CU08.
5. **Validaciones separadas.** Inventariá los artefactos OpenSpec activos y ejecutá `openspec validate --all --strict`, con una línea base previa si es posible. Informá qué validó el CLI, el conteo y el resultado, separando fallos previos de los introducidos. Comprobá también la carga de la configuración. Para la documentación, verificá diez IDs únicos, una ficha por ID, enlaces relativos válidos, trazabilidad de escenarios y alcance y whitespace del diff, incluidos archivos nuevos. Registrá bloqueos o inventario vacío sin atribuirles cobertura.
6. **Cierre documental.** Actualizá `docs/STATE.md` con evidencias, enlaces, pendientes, bloqueos y próximos pasos dentro de sus límites. Informá en pocas líneas archivos editados, resultados y conteos de ambas validaciones, decisiones pendientes y estado final. Detenete al dejarlo listo para revisión humana. Esta etapa autoriza `openspec/config.yaml` y la documentación necesaria bajo `docs/`. Quedan fuera la implementación, instalación de herramientas, apertura de changes de implementación, edición de `AGENTS.md`, modificaciones de otros changes, Apply, Sync, Archive, commit y push.
