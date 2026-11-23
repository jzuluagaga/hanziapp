# E06 · No perder nada

**Tope de extensión:** 160 líneas. **Estado:** primera versión (22 nov 2026).

La causa de abandono del MVP anterior. Atraviesa lectura, escucha y escritura.

---

### HU-E06-01 · Cada respuesta queda guardada
**Como** estudiante **quiero** que no se pierda ninguna respuesta si se cae la red o cierro la pestaña **para** no repetir lo que ya hice.
**Corte:** V1a · **Tipo:** U · **Reglas:** R-SES-03, R-SES-04, R-SES-11 · **Necesita:** HU-E00-01

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado una red lenta, cuando responde, entonces la siguiente tarjeta aparece sin esperar al servidor | `e2e_next_card_does_not_wait_for_network` |
| 2 | Dado respuestas sin red, cuando recarga o cierra la pestaña, entonces siguen en el buzón local y se reenvían solas al volver la red | `e2e_e06_01_outbox_survives_reload` |
| 3 | Dado una respuesta reenviada tarde, cuando llega, entonces se usa la hora del dispositivo solo si cae entre el inicio de la sesión y la recepción; si no, la del servidor | `test_e06_01_client_time_clamped` |
| 4 | Dado una respuesta confirmada tras reintentos, cuando se aplica, entonces se emite `answer_delivery_delayed` con intentos y demora | `test_e06_01_delayed_delivery_event` |
| 5 | Dado respuestas por confirmar, cuando estudia, entonces un indicador discreto lo muestra y desaparece al confirmarse | `e2e_e06_01_pending_indicator` |

- **Derechos:** no aplica.
- **Idioma:** claves `sync.*`.
- **Guardado:** es el objeto de la historia: buzón en `localStorage` (`D-44`) con reenvío y espera creciente.
- **Analítica:** `answer_delivery_delayed`, `answer_recorded`.
- **Datos personales:** el buzón local solo guarda identificadores y calificaciones, y se vacía al confirmarse o al cerrar el acceso.
- **Fuera de alcance:** iniciar sesiones sin red (`R-SES-04`).

### HU-E06-02 · Reanudar donde quedé, o descartar
**Como** estudiante **quiero** volver a la tarjeta exacta donde quedé, o cerrar la sesión conservando lo hecho, **para** que interrumpir no me cueste nada.
**Corte:** V1a · **Tipo:** U · **Reglas:** R-SES-05, R-SES-06, R-SES-08, R-SES-09, R-ESC-07 · **Necesita:** HU-E06-01

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado una sesión en curso para un alcance y una habilidad, cuando pide otra igual, entonces se le ofrece reanudar o descartar y no se crea una segunda | `test_e06_02_one_active_session_per_scope_and_skill` |
| 2 | Dado una sesión a medias, cuando la reanuda, entonces continúa en la primera tarjeta sin responder con el mismo orden y sin recalcular la cola | `test_e06_02_resume_at_first_unanswered` |
| 3 | Dado tarjetas que ya repasó hoy por otra vía, cuando reanuda, entonces se saltan y se marcan como "ya repasada" | `test_e06_02_resume_skips_already_reviewed` |
| 4 | Dado una sesión descartada, cuando se consulta, entonces lo respondido se conserva y la sesión ya no es reanudable | `test_e06_02_discard_keeps_answers` |
| 5 | Dado `session_ttl_days` sin actividad, cuando corre la tarea de caducidad, entonces la sesión caduca con su evento | `test_e06_02_session_expires_after_ttl` |
| 6 | Dado una sesión de ayer sin terminar, cuando la reanuda hoy, entonces sigue siendo válida y cada respuesta cuenta para el día en que se da | `test_e06_02_resumable_across_days` |
| 7 | Dado una sesión de lectura cerrada a la mitad, cuando vuelve en el mismo u otro dispositivo, entonces está en la primera sin responder | `e2e_resume_exact_recognition` |
| 8 | Dado una sesión de escucha cerrada a la mitad, cuando vuelve, entonces está en la primera sin responder | `e2e_resume_exact_listening` |

- **Derechos:** al reanudar no se vuelven a comprobar derechos: la cola ya se armó con ellos.
- **Idioma:** claves `session.conflict.*`, `today.resume.*`.
- **Guardado:** la posición se guarda con cada respuesta confirmada.
- **Analítica:** `session_resumed`, `session_discarded`, `session_expired`.
- **Datos personales:** no guarda nada nuevo.
- **Fuera de alcance:** reanudar un carácter a medio trazar (`R-ESC-07`).

### HU-E06-03 · Seguir en otro dispositivo
**Como** estudiante **quiero** empezar en el computador y terminar en el teléfono **para** estudiar donde esté.
**Corte:** V1a · **Tipo:** U · **Reglas:** R-SES-07 · **Necesita:** HU-E06-02

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado una sesión empezada en un dispositivo, cuando la abre en otro, entonces la reanuda en la misma tarjeta | `test_e06_03_resume_from_other_device` |
| 2 | Dado dos dispositivos con la misma sesión, cuando ambos responden la misma tarjeta, entonces gana la primera respuesta y la segunda se rechaza sin efecto devolviendo la posición actual | `test_e06_03_stale_answer_rejected_with_position` |
| 3 | Dado un dispositivo rechazado, cuando recibe la sesión actual, entonces se reubica en la primera tarjeta sin responder | `e2e_e06_03_rejected_device_relocates` |

- **Derechos:** no aplica.
- **Idioma:** clave `session.relocated`.
- **Guardado:** el servidor manda; el dispositivo descarta su respuesta rechazada.
- **Analítica:** `answer_rejected_stale`, `session_resumed`.
- **Datos personales:** no guarda nada nuevo.
- **Fuera de alcance:** fusionar respuestas de dos dispositivos.
