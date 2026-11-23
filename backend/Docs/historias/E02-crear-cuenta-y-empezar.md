# E02 · Crear cuenta y empezar

**Tope de extensión:** 160 líneas. **Estado:** primera versión (22 nov 2026). En V1 solo se detallan HU-E02-01 y HU-E02-02.

---

### HU-E02-01 · Crear mi cuenta
**Como** alumno de una clase **quiero** registrarme con mi correo desde el enlace que me dio el profesor **para** empezar a estudiar ese mismo día.
**Corte:** V1a · **Tipo:** U · **Reglas:** R-CTA-05, R-CTA-10, R-DAT-01, R-DAT-02, R-DAT-03, R-CTA-03, R-CTA-04 · **Necesita:** HU-E00-03, HU-E00-04

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado el formulario, cuando falta aceptar la política vigente o declarar la mayoría de edad, entonces no se crea la cuenta y se indica cuál falta | `test_e02_01_requires_policy_and_adult` |
| 2 | Dado datos válidos, cuando se registra, entonces se crean la cuenta, el perfil con valores iniciales, la concesión Free, la aceptación de la política con su versión y un consentimiento por finalidad, con los opcionales desmarcados salvo que los marque | `test_e02_01_creates_account_profile_grant_consents` |
| 3 | Dado un enlace con código de cohorte, cuando se registra, entonces la cohorte queda en la cuenta y acompaña a sus eventos | `test_e02_01_cohort_saved_and_in_events` |
| 4 | Dado un correo ya registrado, cuando se intenta otra vez, entonces se rechaza con `email_taken` y no se crea una segunda cuenta | `test_e02_01_duplicate_email_rejected` |
| 5 | Dado una contraseña débil, cuando se envía, entonces se rechaza con `weak_password` | `test_e02_01_weak_password_rejected` |
| 6 | Dado la página de registro, cuando la visita un buscador, entonces pide no ser indexada | `e2e_signup_page_is_noindex` |

- **Derechos:** toda cuenta nueva recibe la concesión por defecto Free (`R-DER-05`).
- **Idioma:** claves `signup.*` y las de error; no depende del idioma de estudio.
- **Guardado:** si la red cae al enviar, el formulario conserva lo escrito y no se crea nada a medias: la cuenta, su perfil, su concesión y sus consentimientos se crean en una sola transacción.
- **Analítica:** `account_registered`, `policy_accepted`.
- **Datos personales:** nombre, correo, contraseña derivada, cohorte, aceptación y consentimientos; se borran con la cuenta (`HU-E10-03`).
- **Fuera de alcance:** conservar lo hecho como invitado (`R-CTA-03`, V2); verificación de correo (V2).

### HU-E02-02 · Acceder y recuperar mi contraseña
**Como** estudiante **quiero** entrar, salir y recuperar el acceso sin ayuda **para** estudiar desde cualquier dispositivo.
**Corte:** V1a · **Tipo:** U · **Reglas:** R-CTA-01, R-CTA-08, R-CTA-09 · **Necesita:** HU-E02-01

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado credenciales correctas, cuando accede, entonces recibe sus credenciales de acceso y la interfaz las guarda solo en cookie httpOnly | `test_e02_02_login_returns_tokens` |
| 2 | Dado cinco intentos fallidos en quince minutos, cuando intenta otra vez, entonces el acceso a ese correo se bloquea quince minutos con el mismo mensaje exista o no el correo | `test_login_lockout` |
| 3 | Dado una cuenta suspendida, cuando intenta acceder con la contraseña correcta, entonces se rechaza con `account_suspended` y sus datos siguen intactos | `test_e02_02_suspended_account_cannot_login` |
| 4 | Dado una solicitud de recuperación, cuando se envía, entonces la respuesta es la misma exista o no el correo; el enlace fija una contraseña nueva una sola vez | `test_e02_02_password_reset_flow` |
| 5 | Dado muchas peticiones seguidas a registro, acceso o recuperación desde una dirección, cuando se pasa el límite, entonces se responde `rate_limited` | `test_rate_limit_auth_endpoints` |
| 6 | Dado un estudiante con acceso, cuando cierra el acceso, entonces se borran las cookies y las rutas privadas lo llevan a acceder | `e2e_logout_clears_access` |

- **Derechos:** no aplica.
- **Idioma:** claves `login.*`, `recover.*` y las de error.
- **Guardado:** no aplica.
- **Analítica:** `login_succeeded`, `login_failed`, `password_reset_completed`.
- **Datos personales:** guarda los intentos fallidos por correo durante la ventana de bloqueo; no se guarda la dirección de red en eventos.
- **Fuera de alcance:** acceso con Google (`HU-E02-03`, V2).
