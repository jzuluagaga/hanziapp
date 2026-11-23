# E05 · Escribir caracteres

**Tope de extensión:** 160 líneas. **Estado:** primera versión (22 nov 2026).

---

### HU-E05-01 · Practicar con guía
**Como** estudiante **quiero** trazar un carácter siguiendo su contorno **para** aprender el orden de trazos sin presión.
**Corte:** V1b · **Tipo:** U · **Reglas:** R-ESC-02, R-ESC-06, R-CON-12 · **Necesita:** HU-E03-01

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado una respuesta con guía, cuando se guarda, entonces queda registrada y no cambia el estado de repaso, el límite de nuevas ni el día activo | `test_e05_01_guided_does_not_change_state` |
| 2 | Dado caracteres sin datos de trazos, cuando se arma la cola de escritura, entonces se omiten y se informa cuántos | `test_e05_01_chars_without_strokes_skipped` |
| 3 | Dado un carácter nuevo, cuando aparece, entonces se presenta primero con guía, sin calificación, y enseguida de memoria | `e2e_e05_01_new_char_guided_then_recall` |

- **Derechos:** solo caracteres de palabras de niveles permitidos.
- **Idioma:** la palabra de contexto muestra su significado en el idioma de estudio.
- **Guardado:** la unidad de guardado es el carácter (`R-ESC-07`).
- **Analítica:** `answer_recorded` con `mode = guided`.
- **Datos personales:** respuestas de escritura; se borran con la cuenta.
- **Fuera de alcance:** reconocimiento de escritura libre sin plantilla.

### HU-E05-02 · Escribir de memoria
**Como** estudiante **quiero** trazar sin ayuda y que el sistema decida si recordé **para** no calificarme con indulgencia.
**Corte:** V1b · **Tipo:** U · **Reglas:** R-ESC-01, R-ESC-03, R-ESC-04, R-ESC-08 · **Necesita:** HU-E05-01

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado un carácter de memoria, cuando se completa, entonces el servidor califica "Recordé" si no hubo pista y hubo `writing_max_stroke_misses` trazos errados o menos, y "No recordé" en otro caso, aunque el dispositivo diga otra cosa | `test_e05_02_server_decides_writing_grade` |
| 2 | Dado una respuesta de memoria, cuando se guarda, entonces conserva los trazos errados, si hubo pista y el umbral vigente | `test_e05_02_answer_stores_threshold` |
| 3 | Dado un carácter que aparece en varias palabras de la cola, cuando se arma, entonces se pide una sola vez | `test_e05_02_char_asked_once_per_queue` |
| 4 | Dado que sale a mitad de un carácter, cuando vuelve, entonces ese carácter empieza limpio y el intento parcial no cuenta | `e2e_resume_exact_writing` |

- **Derechos:** solo niveles permitidos.
- **Idioma:** claves `writing.*`.
- **Guardado:** por carácter; lo trazado a medias no se guarda.
- **Analítica:** `answer_recorded`, `writing_char_abandoned`.
- **Datos personales:** respuestas de escritura; se borran con la cuenta.
- **Fuera de alcance:** calificar la estética del trazo.

### HU-E05-03 · Pedir una pista
**Como** estudiante **quiero** pedir una pista **para** desatascarme sabiendo que cuenta como fallo.
**Corte:** V1b · **Tipo:** U · **Reglas:** R-ESC-05 · **Necesita:** HU-E05-02

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado una respuesta de memoria con pista, cuando se califica, entonces es "No recordé" | `test_e05_03_hint_means_fail` |
| 2 | Dado `auto_hint_after_misses` trazos errados seguidos en el mismo trazo, cuando ocurre el siguiente, entonces aparece una pista automática que cuenta como pista | `e2e_e05_03_auto_hint_after_misses` |
| 3 | Dado una pista mostrada, cuando el navegador lo comunica, entonces se guarda `writing_hint_shown` con `auto` y sin más datos | `test_e05_03_hint_event_schema` |

- **Derechos:** no aplica.
- **Idioma:** claves `writing.hint*`.
- **Guardado:** la pista viaja con la respuesta del carácter.
- **Analítica:** `writing_hint_shown`.
- **Datos personales:** no guarda nada nuevo.
- **Fuera de alcance:** pistas de significado o de pronunciación.
