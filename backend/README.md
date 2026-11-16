# CU04 backend contract

CU04 adds owner-only `GET /domiciles/{d}/management`,
`PATCH /domiciles/{d}`, `GET` and `POST /domiciles/{d}/meters`, and
`GET` and `PATCH /domiciles/{d}/meters/{m}`. The original domicile list and
creation responses remain unchanged. All requests require the existing session;
writes additionally require a trusted Origin and session-bound CSRF token.
Missing, foreign and mismatched resources return the same 404 response.

The domicile management response contains `id`, `display_address`, and `version`;
its PATCH requires `display_address` and a strict positive integer `version`.
Meter responses contain `id`, `domicile_id`, `meter_number`, `alias`, and `version`.
Meter creation accepts `meter_number` and optional `alias`; correction requires
all three of `meter_number`, `alias` (nullable), and `version`. Unknown fields
are rejected. Every successful correction increments its version once, including
an unchanged correction. Stale corrections return 409 with `detail` and
`code: VERSION_CONFLICT`.

Numbers must consist exclusively of printable ASCII before end-space trimming;
after trimming ASCII spaces they must contain 1–120 characters. Case, internal
spaces, punctuation and leading zeros are retained. Duplicate detection is
account-wide, using ASCII-only case folding and ASCII-space trimming. Duplicate
meter writes return 409 with `detail` and `code: DUPLICATE_METER`. Alias accepts
null or Unicode text, rejects control characters before whitespace trimming,
converts blank text to null, and permits at most 120 characters after trimming.

Revision `0002_cu04` is additive to `0001_cu09`; it does not delete data, require
meters, or change interruption associations. Destructive downgrade is not supported.
The optional populated-upgrade test requires `TEST_CU04_MIGRATION=1` and an
isolated synthetic `TEST_DATABASE_URL` with schema-creation permission. It retains
a uniquely named synthetic schema; do not run it on a real-data database. See the
root README for the existing verification-image and synthetic acceptance workflow.

## Operación local y verificaciones

Esta guía reúne los procedimientos técnicos trasladados desde el README principal
el 16/11/2026. Los comandos se ejecutan con PowerShell desde la raíz del repositorio,
salvo indicación expresa. La [puesta en marcha completa](../README.md#2-puesta-en-marcha)
explica la instalación nueva con ambos archivos Compose; estos procedimientos no
constituyen una nueva ejecución ni reemplazan las evidencias de cada cambio.

### Conexión, esquema y configuración

- `compose.yaml` define servicios y almacenamiento. `compose.cu09.yaml` entrega
  `CU09_DATABASE_URL` al backend como `DATABASE_URL`; mantener ambos archivos al
  recrear la aplicación. El archivo base solo no configura la conexión de negocio.
- La URL usa el driver `postgresql+psycopg://`, el host interno `db`, el puerto
  `5432` y el rol/base elegidos. No publicar la URL completada en documentación,
  conversaciones ni logs. El frontend no recibe credenciales de PostgreSQL.
- El usuario inicial creado con `POSTGRES_USER` tiene privilegios administrativos.
  Si se utiliza un rol de aplicación no superusuario, provisionar previamente su
  base y hacer que el administrador cree `vector` en ella antes de migrar.
  La migración `0007_cu03` necesita esa extensión. Los ejecutores de aceptación
  realizan esta preparación solo en sus bases sintéticas recién creadas.
- `alembic upgrade head` prepara la base seleccionada. Las revisiones territoriales
  `0009_territorial_catalog` y `0010_territorial_alias_party_fk` incorporan el catálogo
  compartido y sus alias; no ejecutar migraciones sobre datos existentes como prueba.
  La [bitácora territorial](../docs/ai-engineering/unify-territorial-catalog.md)
  distingue la comprobación realizada de la revisión independiente pendiente.
- `CU09_APP_ORIGINS` configura una lista explícita separada por comas; no utilizar
  `*`. Las cookies locales son HttpOnly/SameSite=Lax. `CU09_COOKIE_SECURE=true`
  corresponde a HTTPS; el entorno Compose documentado usa HTTP de loopback.
- Las variables de inicialización de PostgreSQL actúan sobre un directorio vacío.
  Editar `.env` no rota contraseñas de una base existente. PostgreSQL 18 monta
  `pgdata` en `/var/lib/postgresql`, sin puerto publicado al host.

### Cuentas y administración

El registro público permite crear una cuenta `user` y requiere iniciar sesión
después. La aceptación sintética focalizada e integral de registro/CU04/CU09 pasó;
la suite backend amplia permanece en FAIL (476 PASS, 8 FAIL, 7 SKIP de 491), con
fallos ajenos al registro pendientes en CU01/CU02. Consultá la
[bitácora de registro](../docs/ai-engineering/add-public-account-registration.md).
Se conserva el alta controlada por CLI; solicita la contraseña de forma privada:

```powershell
docker compose -f compose.yaml -f compose.cu09.yaml exec backend python -m app.provision --username cuenta-local
```

Para promover una cuenta ya existente al rol `admin`, el comando es:

```powershell
docker compose -f compose.yaml -f compose.cu09.yaml exec backend python -m app.promote --username cuenta-local
```

La promoción es una acción administrativa deliberada, no un paso obligatorio del
inicio normal. No recibe el rol por argumento ni hay interfaz de autoasignación.
Volver a iniciar sesión para obtener el rol actualizado en la interfaz de CU10.

### Servicios, archivos privados y reinicios

El backend debe ejecutarse en su imagen Linux: el bloqueo de fotos y la
decodificación acotada importan `fcntl` y `resource`, no disponibles de forma
nativa en Windows. Docker Desktop permite usar estos contenedores desde PowerShell.

- `cu05_photos` se monta en `/var/lib/energia-sur/photos`; `cu06_bills`, en
  `/var/lib/energia-sur/bills`. Conservarlos junto con `pgdata`.
- CU05 combina bloqueos de PostgreSQL y del sistema de archivos. La reconciliación
  inicial elimina únicamente objetos que puede demostrar que no están referenciados.
  CU06 tiene su propia reconciliación y falla de forma conservadora si faltan
  referencias o archivos necesarios. El detalle está en las bitácoras de
  [lecturas](../docs/ai-engineering/record-cu05-meter-readings.md) y
  [facturas](../docs/ai-engineering/record-cu06-electricity-bills.md).
- Los workers de fotos/OCR requieren cgroup v2 con swap deshabilitado y core dumps
  deshabilitados. Compose configura memoria, swap y `ulimits`; las instancias que
  compartan datos CU05 deben compartir también el volumen privado.
- `app.start` genera una clave CU06 por proceso si no se suministra
  `CU06_CONFIRMATION_SECRET`. Reiniciar invalida las confirmaciones de solapamiento
  pendientes; una clave configurada explícitamente sigue siendo solo del backend.
- CU06 tiene un ensayo sintético de respaldo/restauración coordinados de base y
  volumen, con el backend detenido. El README anterior conservaba como no probado
  el ensayo equivalente de CU05 y el reinicio en condiciones de producción; no se
  los presenta como comprobados en esta reorganización.

Los montajes de código fuente no incorporan dependencias de Windows. Vite sirve
los cambios de React; después de editar Python, reiniciar el backend:

```powershell
docker compose -f compose.yaml -f compose.cu09.yaml restart backend
```

Los cambios de manifiestos/configuración requieren reconstruir imágenes. Si el
seguimiento de archivos de Windows no detecta un cambio, reconstruir y comprobar
el resultado. Las instalaciones de las imágenes usan `npm ci` y `uv sync --locked`;
no regeneran los lockfiles. Las imágenes están fijadas por digest para `linux/amd64`.

`OUTAGE_SCHEDULER_ENABLED` y `SCHEDULED_WORKS_SCHEDULER_ENABLED` habilitan los dos
actualizadores en Compose. Sus intervalos efectivos están persistidos en
`es_source_config`, se releen en cada ciclo y pueden cambiarse mediante CU10 entre
5/10/15/30/60 minutos. Las variables `OUTAGE_REFRESH_SECONDS` y
`SCHEDULED_WORKS_REFRESH_SECONDS` todavía aparecen en Compose, pero el código ya
no las lee como intervalo. No equivalen a una configuración efectiva.

La resolución por dirección/coordenadas usa solicitudes con cuerpo, sin registrar
esos datos. Su límite por proceso usa el peer de conexión (20/minuto); tras el proxy
Vite el tráfico del navegador comparte ese peer. La identificación del cliente para
un alojamiento multiusuario sigue siendo una consideración pendiente.

### Guía y memoria del asistente

La [guía aprobada](knowledge/guia-oficial-edesur.md) tiene identificador
`energia-sur-kb-edesur-001`, versión `1.0.0` y fecha de verificación `2026-11-10`.
La ingesta trabaja por artículo (53 unidades en la verificación registrada), es
idempotente, controla versiones y rechaza retroceder a una versión anterior salvo
uso explícito de `--force`. No hay que forzar la ingesta en el inicio normal.

El comando manual y la opción `ASSISTANT_GUIDE_INGEST=true` se describen en el
[README principal](../README.md#acceso-y-asistente-opcional). Los demás límites
`ASSISTANT_*` están definidos en [Compose](../compose.yaml) y en
[`app/assistant_limits.py`](app/assistant_limits.py).
El índice actual usa vectores de 1536 dimensiones: cambiar el modelo de embeddings
no es intercambiable automáticamente con un índice ya generado.

La memoria de visitantes es temporal y reside en Zustand, con TTL de 30 minutos
por defecto. `ASSISTANT_VISITOR_TTL_MINUTES` configura el argumento de construcción
`VITE_ASSISTANT_TTL_MINUTES`; reconstruir el frontend para modificarlo.
Las conversaciones autenticadas se persisten por propietario. Las operaciones de
listado, lectura y borrado están disponibles por API; no hay una interfaz de listado
o restauración de conversaciones. `ASSISTANT_RETENTION_DAYS` documenta una propuesta
de 30 días, no un borrado automático aprobado: los mensajes permanecen hasta que
su propietario los borra. Ver [CU03](../docs/ai-engineering/implement-integrated-assistant-cu03.md).

### Aceptación con datos sintéticos

Construir primero las imágenes de verificación. No sustituirlas por las de runtime,
que excluyen herramientas de desarrollo necesarias para Ruff/mypy e inspección PDF:

```powershell
docker build --target verification -t energia-sur-backend-checks:cu09 backend
docker build --target verification -t energia-sur-frontend-checks:cu09 frontend
pwsh -NoProfile -File scripts/Test-Cu09Acceptance.ps1
# Selección focalizada de registro público:
pwsh -NoProfile -File scripts/Test-Cu09Acceptance.ps1 -BackendTestPattern test_registration.py -E2ETestPattern e2e/public-registration.spec.ts
```

Revisar [`Test-Cu09Acceptance.ps1`](../scripts/Test-Cu09Acceptance.ps1) antes de
ejecutarlo: necesita la base Compose en ejecución y crea bases, un rol no
privilegiado y cuentas sintéticas. Instala `vector` como administrador solo en esas
bases, migra, ejecuta pruebas PostgreSQL/ASGI, recrea frontend/backend para QA y
conduce Chromium. Desactiva actualizadores e ingesta durante la aceptación aislada.
La ejecución completa incluye inspección de PDF, migración con datos y persistencia
tras reinicio. Los patrones focalizados omiten esas comprobaciones integrales.

Conserva bases sintéticas, contenedores de QA y artefactos bajo el directorio
temporal local de OpenCode; no limpia bases/tablas/volúmenes. La aplicación queda
conectada a la base sintética de aceptación y no a una cuenta con datos reales.
No reemplaza el contenedor PostgreSQL original, pero añade recursos al clúster.
Consultar [STATE](../docs/STATE.md) y la [bitácora de registro](../docs/ai-engineering/add-public-account-registration.md)
para los resultados recientes. La pasada amplia más reciente está documentada como
FAIL; la aceptación seleccionada de registro/CU04/CU09, incluidos PDF y persistencia,
pasó sin afirmar que la suite completa esté validada.

### Ejecutor focalizado CU05/CU06

```powershell
docker build --target verification -t energia-sur-backend-checks:cu10 backend
pwsh -NoProfile -File scripts/Test-Cu05Cu06BackendRuntime.ps1
```

Requiere el contenedor `energia-sur-db-1` en ejecución y usa por defecto la imagen
`energia-sur-backend-checks:cu10`. Crea un rol/base únicos y almacenamiento privado
tmpfs, genera una clave CU06 sintética de 32 bytes y verifica `RLIMIT_CORE == 0`
y `memory.swap.max == 0`. Ejecuta individualmente los seis tests históricos.
Los informes y logs se conservan en
`$env:LOCALAPPDATA\Temp\opencode\cu05-cu06-runtime`.

`-Rebuild` reconstruye la imagen, `-MemoryLimit` ajusta los 2 GB predeterminados y
`-Cleanup` elimina únicamente la base y el rol sintéticos creados en esa ejecución;
sin esa opción se conservan. No se ejecutó ninguna limpieza en esta refactorización.
El ejecutor no recrea, reinicia ni elimina los servicios compartidos.

La [bitácora de estabilización](../docs/ai-engineering/stabilize-cu05-cu06-backend-test-runtime.md)
registra 6/6 focalizados, 32 pruebas CU06 con una omisión y 45/45 CU05.
Son resultados históricos, no una promesa sobre una nueva ejecución. No cubren el
defecto visual del historial CU05; su [corrección y nueve E2E](../docs/ai-engineering/isolate-cu05-reading-history-by-meter.md)
se documentan por separado.

### Pruebas específicas de fuentes y navegador

Dentro de una imagen backend de verificación, los comandos de selección son:

```powershell
python -m unittest discover -s tests -p 'test_cu01_*.py'
python -m unittest tests.test_cu02_scheduled_works
```

Las pruebas API/PostgreSQL necesitan un `TEST_DATABASE_URL` sintético y migrado;
`TEST_ENRE_LIVE=1` y `TEST_GEOREF_LIVE=1` habilitan las consultas reales correspondientes.
Las omisiones por requisitos ausentes no acreditan aceptación. Las instrucciones
y evidencias están en [CU01](../docs/ai-engineering/implement-current-outages-cu01.md),
[CU02](../docs/ai-engineering/implement-scheduled-works-cu02.md) y el
[catálogo territorial](../docs/ai-engineering/unify-territorial-catalog.md).

En un contenedor frontend de verificación con servidor alcanzable se pueden
seleccionar suites con los scripts reales del manifiesto:

```powershell
npm run test:e2e -- e2e/cu01.spec.ts e2e/cu02.spec.ts
```

Esas suites usan contratos simulados. `e2e/cu01-real.spec.ts` requiere `CU01_LIVE=1`,
una base aislada con la captura sintética `tests/fixtures/enre_data_eds_redacted.js`
cargada mediante `app.outage_store._store_snapshot`, y el backend alcanzable como
`backend:8000` por el proxy. Las suites reales CU04/CU06/CU07/CU08 requieren cuentas
sintéticas, y CU07/CU08 también sus archivos de estado; CU10 necesita cuentas con
roles distintos. No ejecutar toda la colección sin preparar esos requisitos.

### Comprobaciones de infraestructura

Estos comandos históricos complementan la aceptación funcional; se conservan aquí
para no confundir una comprobación HTTP con una aplicación completa:

```powershell
docker compose -f compose.yaml -f compose.cu09.yaml exec -T backend python -m unittest discover -s tests -p test_health.py -v
docker compose -f compose.yaml -f compose.cu09.yaml exec -T frontend npm run typecheck
docker compose -f compose.yaml -f compose.cu09.yaml exec -T frontend npm test
docker compose -f compose.yaml -f compose.cu09.yaml exec -T frontend npm run build
pwsh -NoProfile -File scripts/Test-Lockfiles.ps1
pwsh -NoProfile -File scripts/Test-HealthProxy.ps1
pwsh -NoProfile -File scripts/Test-DatabasePersistence.ps1
```

- `Test-Lockfiles.ps1` modifica copias desechables en contenedores para comprobar que
  las instalaciones bloqueadas rechazan cambios inconsistentes.
- `Test-HealthProxy.ps1` consulta `/health` directo y por `/api/health`, detiene solo
  el backend para comprobar el error y lo restaura en `finally`. No inspecciona UI.
  El control de salud dejó de ser contenido de la interfaz por U26.
- `Test-DatabasePersistence.ps1` añade un marcador sintético a una tabla técnica,
  recrea solo `db`, conserva el volumen y comprueba la identidad del marcador.
  Modifica la base y reinicia el contenedor; no es una comprobación de solo lectura.

Para comprobar manualmente el proxy, consultar `/api/health` y `/health`, detener
el backend, confirmar que el proxy ya no devuelve éxito y restaurar el mismo
contenedor con `docker compose start backend`; no recrearlo con el archivo base
solo. El comando `stop` conserva el entorno de la instancia existente.
Los pasos y resultados históricos se mantienen en la
[bitácora Docker](../docs/ai-engineering/docker-development-environment.md).
Su cambio sigue abierto y conserva tareas de cierre por reconciliar; los controles
Ruff/mypy/Oxlint aprobados después bajo CU09 no lo cierran automáticamente.
