# E04 · Escuchar

**Tope de extensión:** 160 líneas. **Estado:** primera versión (22 nov 2026).

---

### HU-E04-01 · Oír la palabra y su ejemplo
**Como** estudiante **quiero** oír cualquier palabra o ejemplo cuando lo pido **para** aprender cómo suena.
**Corte:** V1a · **Tipo:** U · **Reglas:** R-CON-13, R-IDI-08 · **Necesita:** HU-E13-02

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado una palabra con audio, cuando la API la devuelve en una tarjeta o ficha, entonces trae la dirección del audio de la palabra y de cada ejemplo, o nada si no existe | `test_e04_01_card_payload_includes_audio_urls` |
| 2 | Dado una tarjeta de lectura, cuando aparece, entonces el audio no suena solo: suena al pedirlo | `e2e_e04_01_audio_plays_on_request` |
| 3 | Dado un audio que no carga, cuando se pide, entonces se avisa sin bloquear la tarjeta y se emite `audio_failed` | `e2e_e04_01_audio_failure_does_not_block` |
| 4 | Dado dos audios del mismo texto con distinta voz o idioma, cuando se guardan, entonces coexisten | `test_audio_keyed_by_language_and_voice` |

- **Derechos:** el audio no depende del plan (`R-CON-09`).
- **Idioma:** el audio es en chino; claves `audio.*`.
- **Guardado:** no aplica.
- **Analítica:** `audio_played`, `audio_failed`.
- **Datos personales:** no aplica; el audio de contenido no es dato personal.
- **Fuera de alcance:** ajustar la velocidad de reproducción.

### HU-E04-02 · Oír y elegir
**Como** estudiante **quiero** oír una palabra y elegir su significado **para** reconocerla al oído, que es media prueba de HSK 1 y 2.
**Corte:** V1a · **Tipo:** U · **Reglas:** R-REP-01, R-REP-07 · **Necesita:** HU-E03-02, HU-E04-01

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado una palabra con audio y su primer "Recordé" en lectura ayer o antes, cuando se arma una sesión de escucha, entonces es elegible; si no tiene audio o el primer "Recordé" es de hoy, no | `test_e04_02_listening_eligibility` |
| 2 | Dado una tarjeta de escucha, cuando se presenta, entonces ofrece cuatro opciones: la correcta y tres palabras publicadas del mismo nivel, y elegir la correcta es "Recordé" según decide el servidor | `test_e04_02_choices_from_same_level` |
| 3 | Dado respuestas en escucha, cuando se aplican, entonces cambian su propio estado sin tocar el de lectura | `test_e04_02_listening_has_own_state` |
| 4 | Dado muchas palabras elegibles por primera vez, cuando se arma la cola, entonces no se aplica límite de nuevas en escucha | `test_e04_02_no_new_limit_for_listening` |

- **Derechos:** solo niveles permitidos.
- **Idioma:** las opciones se muestran en el idioma de estudio.
- **Guardado:** igual que lectura (`HU-E06-01`).
- **Analítica:** `answer_recorded` (con el campo de repeticiones del audio), `audio_played`.
- **Datos personales:** respuestas y estado de escucha; se borran con la cuenta.
- **Fuera de alcance:** dictado o escribir lo que se oye.
