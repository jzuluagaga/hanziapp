# E00 · Cimientos

**Tope de extensión:** 160 líneas. **Estado:** primera versión (22 nov 2026).

Lo que debe existir antes de la primera pantalla para no pagar deuda después.

---

### HU-E00-01 · Respuestas que se aplican una sola vez
**Como** estudiante **quiero** que reintentar un envío nunca duplique un repaso **para** confiar en mi calendario aunque la red falle.
**Corte:** V1a · **Tipo:** H · **Reglas:** R-SES-03, R-SES-04, R-DER-09 · **Necesita:** —

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado una respuesta ya aplicada, cuando llega otra con el mismo identificador de cliente, entonces el servidor devuelve el mismo resultado y no crea otra respuesta ni toca el estado de repaso | `test_e00_01_same_client_id_applies_once` |
| 2 | Dado dos filas con el mismo identificador para la misma cuenta, cuando se intenta guardarlas, entonces la base rechaza la segunda por restricción, sin depender del código | `test_e00_01_client_id_unique_in_database` |
| 3 | Dado dos cuentas que usan el mismo identificador, cuando ambas responden, entonces las dos respuestas se aplican | `test_e00_01_client_id_scoped_to_account` |
| 4 | Dado 1.000 respuestas con reenvíos, duplicados y orden alterado, cuando se procesan, entonces hay exactamente 1.000 efectos | `test_answers_exactly_once_under_chaos` |
| 5 | Dado un consumo de cuota ya registrado, cuando se repite con el mismo identificador, entonces se descuenta una sola vez | `test_e00_01_usage_record_applies_once` |

- **Derechos:** no aplica; es un mecanismo común a todas las respuestas y consumos.
- **Idioma:** no añade textos; el rechazo devuelve la clave `stale_card`.
- **Guardado:** es el mecanismo de guardado: un reenvío tras una caída devuelve el resultado ya guardado.
- **Analítica:** `answer_recorded` se emite una sola vez por identificador.
- **Datos personales:** guarda respuestas ligadas a la cuenta; se borran con ella.
- **Fuera de alcance:** sincronización sin conexión de sesiones nuevas (`D-03`).

### HU-E00-02 · Analítica desde el primer día
**Como** dueño **quiero** que cada historia emita eventos **para** calcular retención y aprendizaje desde la primera clase.
**Corte:** V1a · **Tipo:** H · **Reglas:** R-DAT-07, R-IDI-13 · **Necesita:** —

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado una cuenta con cohorte e idiomas, cuando emite un evento, entonces lleva los campos comunes: seudónimo, cohorte, idiomas, plan, día local, cliente y versión | `test_e00_02_events_carry_common_fields` |
| 2 | Dado un evento con un campo no declarado en su esquema, cuando se intenta emitir, entonces se rechaza; ningún esquema admite nombre, correo, texto libre ni audio | `test_event_schemas_have_no_pii` |
| 3 | Dado un hecho cuya transacción se revierte, cuando falla, entonces su evento tampoco queda guardado | `test_e00_02_event_rolls_back_with_fact` |
| 4 | Dado una cuenta, cuando se calcula su seudónimo, entonces no es su identificador ni se deriva de su correo | `test_e00_02_account_key_is_pseudonymous` |
| 5 | Dado el navegador, cuando envía un evento que no está en la lista de eventos del cliente, entonces se rechaza con `event_not_allowed` | `test_e00_02_client_events_whitelist` |

- **Derechos:** no aplica.
- **Idioma:** no añade textos; cada evento lleva los dos idiomas de la cuenta.
- **Guardado:** el evento se escribe en la misma transacción que el hecho; si el hecho no ocurre, no hay evento.
- **Analítica:** define el mecanismo para todos los eventos del catálogo.
- **Datos personales:** solo un seudónimo; al eliminar la cuenta el seudónimo se sustituye por uno aleatorio.
- **Fuera de alcance:** servicios externos de analítica (`D-41`).

### HU-E00-03 · Listo para un segundo idioma
**Como** dueño **quiero** que añadir inglés sea cargar, publicar y encender **para** no tocar código ni esquema cuando llegue el momento.
**Corte:** V1a · **Tipo:** H · **Reglas:** R-IDI-02, R-IDI-03, R-IDI-04, R-IDI-09, R-IDI-10, R-IDI-11 · **Necesita:** —

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado un idioma ficticio con cinco palabras publicadas y sus interruptores encendidos, cuando un estudiante se registra con él, entonces busca, ve una ficha y completa una sesión sin migraciones ni cambios de código | `test_add_language_without_migration` |
| 2 | Dado la interfaz en un idioma y el estudio en otro, cuando el estudiante estudia, entonces cada uno se respeta por separado | `test_ui_and_study_language_independent` |
| 3 | Dado contenido publicado en un idioma, cuando se consulta en otro, entonces no aparece | `test_content_status_independent_per_language` |
| 4 | Dado un mazo del sistema o un nivel, cuando la API lo devuelve, entonces trae una clave y sus parámetros, nunca un nombre escrito | `test_system_names_translated` |
| 5 | Dado cualquier error de la API, cuando se devuelve, entonces lleva una clave de traducción y no un texto | `test_e00_03_server_errors_are_translation_keys` |
| 6 | Dado los catálogos de interfaz cargados, cuando se compilan, entonces todos tienen todas las claves | `test_i18n_catalogs_complete` |

- **Derechos:** no aplica.
- **Idioma:** es el objeto de la historia: catálogos es y en completos, inglés cargado e inactivo.
- **Guardado:** no aplica.
- **Analítica:** no aplica; los idiomas viajan en los campos comunes.
- **Datos personales:** no aplica.
- **Fuera de alcance:** traducir el contenido al inglés (`D-06`).

### HU-E00-04 · Operación segura
**Como** dueño **quiero** un despliegue repetible, interruptores y una ruta de salud **para** operar solo sin sustos.
**Corte:** V1a · **Tipo:** H · **Reglas:** R-DAT-06, R-DER-10, R-CON-15 · **Necesita:** —

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado el servicio en marcha, cuando el monitor consulta la ruta de salud, entonces responde según el estado real de la base | `test_e00_04_health_checks_database` |
| 2 | Dado el interruptor `signup_mode` en `closed`, cuando alguien intenta registrarse, entonces se rechaza sin desplegar | `test_e00_04_signup_switch_closes_registration` |
| 3 | Dado un parámetro ajustable, cuando no tiene fila, entonces rige su valor inicial; cuando se cambia en el panel, queda en auditoría | `test_e00_04_parameter_change_is_audited` |
| 4 | Dado una función con costo variable, cuando se alcanza el tope de gasto o se apaga su interruptor, entonces se pausa para todos y lo demás sigue funcionando | `test_global_budget_pauses_feature` |
| 5 | Dado la aplicación publicada, cuando se abre la página de créditos, entonces nombra el sílabo, Make Me a Hanzi, Hanzi Writer y la síntesis de voz con sus licencias | `e2e_credits_page_lists_licenses` |

- **Derechos:** el freno de costos actúa antes que cualquier cuota por cuenta.
- **Idioma:** la página de créditos sale del catálogo.
- **Guardado:** no aplica.
- **Analítica:** no aplica.
- **Datos personales:** las copias de seguridad caducan en `backup_retention_days`; se configura en la plataforma, fuera del código.
- **Fuera de alcance:** redundancia y alta disponibilidad (`09-arquitectura.md`, sección 8); la restauración de copias se comprueba a mano por corte (`Q-04`).
