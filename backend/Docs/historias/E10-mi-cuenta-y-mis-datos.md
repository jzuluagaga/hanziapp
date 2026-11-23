# E10 · Mi cuenta y mis datos

**Tope de extensión:** 160 líneas. **Estado:** primera versión (22 nov 2026). En V1 se detallan HU-E10-01 a HU-E10-03.

---

### HU-E10-01 · Ajustar mi perfil
**Como** estudiante **quiero** cambiar mi nombre, idiomas, zona horaria y límites diarios **para** adaptar la aplicación a mí.
**Corte:** V1b · **Tipo:** U · **Reglas:** R-IDI-01, R-IDI-12, R-PRO-02, R-REP-06, R-DAT-05 · **Necesita:** HU-E02-01

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado valores dentro de su rango, cuando guarda el perfil, entonces se aplican; fuera de rango se rechazan con `limit_out_of_range` | `test_e10_01_update_profile_within_ranges` |
| 2 | Dado un idioma que no está activo, cuando lo elige, entonces se rechaza con `language_inactive` | `test_e10_01_inactive_language_rejected` |
| 3 | Dado que cambia el idioma de estudio, cuando vuelve a estudiar, entonces conserva todos sus estados y las palabras no publicadas en el nuevo idioma salen de sus colas | `test_e10_01_study_language_change_keeps_states` |
| 4 | Dado que cambia de zona horaria, cuando se calcula el día, entonces la nueva rige desde el día siguiente y no cambia días pasados | `test_e10_01_timezone_change_applies_next_day` |
| 5 | Dado un perfil guardado, cuando se emite el evento, entonces lleva los nombres de los campos cambiados y no sus valores | `test_e10_01_profile_event_has_field_names_only` |

- **Derechos:** no aplica.
- **Idioma:** claves `settings.*`; el idioma de interfaz cambia los textos al instante.
- **Guardado:** si falla el envío, el formulario conserva lo escrito.
- **Analítica:** `profile_updated`.
- **Datos personales:** nombre, idiomas, zona horaria y límites; se exportan (V2) y se borran con la cuenta.
- **Fuera de alcance:** cambiar el correo (exige verificación, V2).

### HU-E10-02 · Controlar mis consentimientos
**Como** estudiante **quiero** leer la política, aceptar sus versiones nuevas y dar o retirar cada consentimiento **para** decidir qué se hace con mis datos.
**Corte:** V1a · **Tipo:** U · **Reglas:** R-DAT-01, R-DAT-02, R-DAT-08, R-DAT-11 · **Necesita:** HU-E02-01

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado una versión nueva de la política, cuando accede, entonces debe aceptarla antes de estudiar y la aceptación guarda versión y fecha | `test_e10_02_new_policy_version_blocks_until_accepted` |
| 2 | Dado los consentimientos por finalidad, cuando cambia uno, entonces los demás no cambian, queda su historial y `general` no se puede retirar sin eliminar la cuenta | `test_e10_02_consents_independent_and_revocable` |
| 3 | Dado una cuenta nueva, cuando se consulta, entonces existe la finalidad `voice_recording`, apagada, sin interfaz visible | `test_e10_02_voice_consent_exists_off_by_default` |
| 4 | Dado grabaciones ficticias vencidas o con el consentimiento revocado, cuando corre la tarea de conservación, entonces se borran en su plazo | `test_retention_jobs` |
| 5 | Dado la página de la política, cuando se abre, entonces nombra a todos los proveedores que tratan datos y su país | `e2e_e10_02_policy_lists_providers` |

- **Derechos:** no aplica.
- **Idioma:** la política existe en cada idioma de interfaz activo; claves `privacy.*`.
- **Guardado:** cada cambio se confirma con el servidor antes de mostrarse como hecho.
- **Analítica:** `policy_accepted`, `consent_changed`.
- **Datos personales:** aceptaciones y consentimientos con fecha; se borran con la cuenta salvo la prueba que exija la ley (**LEGAL**).
- **Fuera de alcance:** grabar la voz (V4).

### HU-E10-03 · Eliminar mi cuenta
**Como** estudiante **quiero** borrar mi cuenta y mis datos de forma definitiva **para** ejercer mi derecho sin pedirlo a nadie.
**Corte:** V1b · **Tipo:** U · **Reglas:** R-DAT-06 · **Necesita:** HU-E10-02

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado una cuenta con datos en todos los módulos, cuando la elimina confirmando su contraseña, entonces no queda ninguna fila vinculada a ella salvo lo que la regla permite sin vínculo | `test_account_deletion_leaves_no_trace` |
| 2 | Dado eventos de la cuenta, cuando se elimina, entonces su seudónimo se sustituye por uno aleatorio y los conteos se conservan | `test_e10_03_events_unlinked` |
| 3 | Dado una contraseña incorrecta, cuando intenta eliminar, entonces la cuenta sigue intacta | `test_e10_03_wrong_password_keeps_account` |
| 4 | Dado reportes y registros de auditoría de la cuenta, cuando se elimina, entonces se conservan sin vínculo con ella | `test_e10_03_audit_and_reports_unlinked` |

- **Derechos:** las concesiones se borran con la cuenta.
- **Idioma:** claves `deleteAccount.*`.
- **Guardado:** todo el borrado ocurre en una transacción; si falla, no se borra nada.
- **Analítica:** `account_deleted`.
- **Datos personales:** es el objeto de la historia.
- **Fuera de alcance:** recuperar una cuenta eliminada.
