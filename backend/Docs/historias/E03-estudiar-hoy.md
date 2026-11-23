# E03 · Estudiar hoy (el núcleo)

**Tope de extensión:** 160 líneas. **Estado:** primera versión (22 nov 2026). En V1 se detallan HU-E03-01 a HU-E03-04.

---

### HU-E03-01 · Ver qué me toca hoy y empezar
**Como** estudiante **quiero** ver lo pendiente de hoy y empezar con un toque **para** no tener que decidir qué repasar.
**Corte:** V1a · **Tipo:** U · **Reglas:** R-REP-04, R-REP-08, R-SES-01, R-SES-02, R-SES-10, R-SES-12 · **Necesita:** HU-E08-01, HU-E11-01

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado tarjetas pendientes y nuevas en varias habilidades, cuando abre "Hoy", entonces ve por habilidad cuántas pendientes y cuántas nuevas tiene, sin contar lo bloqueado ni lo que está en revisión | `test_e03_01_today_counts_by_skill` |
| 2 | Dado pendientes con distinto atraso y nuevas, cuando empieza una sesión, entonces la cola trae primero las pendientes de la más atrasada a la menos y después las nuevas en el orden del mazo, con un máximo de `session_max_cards` | `test_e03_01_queue_order_and_cap` |
| 3 | Dado que no hay nada que estudiar, cuando pide una sesión, entonces no se crea y se dice por qué: nada pendiente, límite de nuevas alcanzado, contenido en revisión o nivel fuera del plan | `test_e03_01_empty_session_reason` |
| 4 | Dado una sesión iniciada, cuando pasan cosas que crearían nuevas pendientes, entonces su cola no cambia salvo por los refuerzos | `test_e03_01_queue_is_frozen_at_start` |
| 5 | Dado "todos los pendientes", cuando hay que enseñar nuevas, entonces salen de los mazos del sistema que el plan permite, en orden de nivel y de mazo | `test_e03_01_all_due_new_words_follow_system_decks` |
| 6 | Dado "Estudiar hoy", cuando termina una habilidad, entonces se ofrece la siguiente con algo pendiente (lectura, escucha, escritura) y puede saltarla | `e2e_study_today_chains_skills` |

- **Derechos:** la cola solo incluye niveles permitidos por el motor de derechos (`HU-E11-01`); lo demás se cuenta como bloqueado.
- **Idioma:** claves `today.*` y `session.empty.*`; las cuentas dependen del idioma de estudio, porque solo cuentan palabras publicadas en él.
- **Guardado:** la sesión y su cola se guardan al crearse; cerrar la pestaña no la pierde (`HU-E06-02`).
- **Analítica:** `home_viewed`, `session_started`, `session_empty`, `entitlement_denied`.
- **Datos personales:** crea sesiones ligadas a la cuenta; se borran con ella.
- **Fuera de alcance:** sesiones de varias habilidades (`D-21`); repaso libre (`HU-E03-06`, V2).

### HU-E03-02 · Repasar una tarjeta de lectura
**Como** estudiante **quiero** ver el hanzi, revelar pinyin y significado y decir si recordé **para** que el sistema programe el próximo repaso.
**Corte:** V1a · **Tipo:** U · **Reglas:** R-REP-01, R-REP-02, R-REP-03, R-REP-05, R-REP-09, R-CON-10 · **Necesita:** HU-E03-01, HU-E00-01

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado una tarjeta, cuando la ve, entonces primero revela pinyin y significado y solo después puede calificar | `e2e_e03_02_reveal_then_grade` |
| 2 | Dado una respuesta, cuando llega al programador, entonces "Recordé" es "Good" y "No recordé" es "Again"; nunca hay otra calificación | `test_e03_02_grades_map_to_good_and_again` |
| 3 | Dado un "No recordé", cuando se responde, entonces la tarjeta reaparece como refuerzo tras `reinforce_gap` tarjetas hasta responder "Recordé", y los refuerzos no cambian el estado | `test_e03_02_failed_card_reinforced_without_state_change` |
| 4 | Dado una tarjeta ya repasada hoy desde otro mazo, cuando se responde otra vez, entonces se registra pero no cambia su único estado de repaso | `test_e03_02_only_first_answer_of_day_counts` |
| 5 | Dado secuencias de referencia, cuando pasan por el adaptador, entonces dan los mismos intervalos que la librería fijada | `test_fsrs_adapter_reference_vectors` |
| 6 | Dado palabras no publicadas en el idioma de estudio, cuando se arma una cola, entonces nunca entran | `test_e03_02_unpublished_words_never_queued` |

- **Derechos:** solo palabras de niveles permitidos.
- **Idioma:** significado y traducciones en el idioma de estudio; claves `card.*`.
- **Guardado:** cada respuesta va al buzón local y al servidor (`HU-E06-01`).
- **Analítica:** `answer_recorded`.
- **Datos personales:** respuestas, historial y estado de repaso; se borran con la cuenta.
- **Fuera de alcance:** deshacer (`HU-E03-05`, V2); "Ya la sé" (retirado, `D-42`).

### HU-E03-03 · Aprender palabras nuevas a mi ritmo
**Como** estudiante **quiero** recibir nuevas hasta mi límite diario **para** no saturarme.
**Corte:** V1a · **Tipo:** U · **Reglas:** R-REP-06, R-REP-03, R-REP-08 · **Necesita:** HU-E03-01

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado un límite de nuevas en lectura, cuando estudia varios mazos el mismo día, entonces el límite cuenta entre todos | `test_e03_03_new_limit_across_decks` |
| 2 | Dado el límite agotado, cuando pide más, entonces la sesión dice `new_limit_reached` y se emite el evento una vez al día por habilidad | `test_e03_03_new_limit_reached_event` |
| 3 | Dado que sube su límite en el perfil, cuando pide otra sesión el mismo día, entonces recibe las nuevas que faltan hasta el límite nuevo | `test_e03_03_limit_change_applies_now` |
| 4 | Dado una tarjeta nueva, cuando la ve, entonces solo puede responder "Recordé" o "No recordé" | `e2e_e03_03_new_card_has_two_grades` |

- **Derechos:** las nuevas solo salen de niveles permitidos.
- **Idioma:** claves `session.empty.new_limit_reached`.
- **Guardado:** el límite se calcula con las respuestas confirmadas del día.
- **Analítica:** `new_limit_reached`, `answer_recorded`.
- **Datos personales:** el límite vive en el perfil.
- **Fuera de alcance:** sugerir el límite según una fecha de examen (`HU-E09-03`, V2).

### HU-E03-04 · Ver cómo me fue
**Como** estudiante **quiero** ver mis aciertos y fallos al terminar **para** saber qué sigue.
**Corte:** V1a · **Tipo:** U · **Reglas:** R-SES-08, R-PRO-03 · **Necesita:** HU-E03-02

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado la última tarjeta respondida, cuando se confirma, entonces la sesión queda completada con aciertos y fallos contados sin refuerzos | `test_e03_04_completion_summary` |
| 2 | Dado una sesión de "Estudiar hoy", cuando termina, entonces el resumen ofrece la siguiente habilidad con algo pendiente | `e2e_e03_04_summary_offers_next_skill` |
| 3 | Dado una sesión descartada a la mitad, cuando se consulta, entonces lo respondido sigue contando en su estado y en el día | `test_e03_04_answers_final_after_discard` |

- **Derechos:** no aplica.
- **Idioma:** claves `summary.*`.
- **Guardado:** el resumen se calcula en el servidor; recargar lo muestra igual.
- **Analítica:** `session_completed`.
- **Datos personales:** no guarda nada nuevo.
- **Fuera de alcance:** comparativas con otros estudiantes.
