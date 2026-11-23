# E07 · Explorar

**Tope de extensión:** 160 líneas. **Estado:** primera versión (22 nov 2026). En V1 se detallan HU-E07-01 a HU-E07-04.

---

### HU-E07-01 · Buscar una palabra
**Como** estudiante **quiero** encontrar una palabra por hanzi, pinyin o significado **para** consultarla cuando la necesito.
**Corte:** V1b · **Tipo:** U · **Reglas:** R-CON-01, R-IDI-07 · **Necesita:** HU-E13-01

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado una consulta con caracteres chinos, cuando busca, entonces encuentra las palabras del sílabo que los contienen | `test_e07_01_search_by_hanzi` |
| 2 | Dado una consulta en pinyin con o sin tonos, cuando busca, entonces encuentra las mismas palabras, primero las exactas | `test_e07_01_search_by_pinyin_with_or_without_tones` |
| 3 | Dado una consulta por significado, cuando busca, entonces busca solo en el idioma de estudio, sin distinguir tildes ni mayúsculas | `test_search_scoped_to_study_language` |
| 4 | Dado una búsqueda, cuando se registra, entonces el evento lleva el tipo de consulta y el número de resultados, nunca el texto | `test_e07_01_search_event_has_no_query_text` |
| 5 | Dado las 5.400 palabras cargadas, cuando se busca con carga, entonces responde en 300 ms o menos en el percentil 95 | `load_dictionary_search` |

- **Derechos:** el diccionario no depende del plan (`R-CON-09`).
- **Idioma:** el significado se busca en el idioma de estudio; claves `dictionary.*`.
- **Guardado:** no aplica.
- **Analítica:** `search_performed`.
- **Datos personales:** no guarda la consulta.
- **Fuera de alcance:** filtrar por nivel (V2); palabras fuera del sílabo (`D-09`).

### HU-E07-02 · Ver la ficha de una palabra
**Como** estudiante **quiero** ver el contenido de una palabra **para** entenderla con ejemplos.
**Corte:** V1b · **Tipo:** U · **Reglas:** R-CON-08, R-CON-02, R-IDI-06 · **Necesita:** HU-E07-01

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado una palabra publicada en el idioma de estudio, cuando abre su ficha, entonces ve acepciones con significado, ejemplos con pinyin y traducción, y audio | `test_e07_02_published_word_detail` |
| 2 | Dado una palabra no publicada en el idioma de estudio, cuando abre su ficha, entonces ve solo hanzi, pinyin, nivel y el aviso "en revisión" | `test_e07_02_unpublished_shows_syllabus_only` |
| 3 | Dado una palabra con glosa de terceros, cuando se consulta por cualquier ruta, entonces la glosa no aparece | `test_e07_02_never_exposes_third_party_gloss` |
| 4 | Dado una cuenta Free, cuando abre la ficha de una palabra de HSK 5, entonces la ve completa | `test_e07_02_dictionary_free_for_all_levels` |

- **Derechos:** ninguno: la ficha es gratuita.
- **Idioma:** significados y traducciones del idioma de estudio, y de ningún otro.
- **Guardado:** no aplica.
- **Analítica:** `word_viewed`.
- **Datos personales:** no aplica.
- **Fuera de alcance:** guardar la palabra en un mazo propio (`HU-E07-05`, V2).

### HU-E07-03 · Ver cómo se traza
**Como** estudiante **quiero** ver la animación del orden de trazos **para** escribir bien cada carácter.
**Corte:** V1b · **Tipo:** U · **Reglas:** R-CON-12 · **Necesita:** HU-E07-02

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado una ficha, cuando pide la animación, entonces se reproduce el orden de trazos de cada carácter | `e2e_e07_03_stroke_animation_per_char` |
| 2 | Dado un carácter sin datos de trazos, cuando se pide, entonces se avisa en lugar de la animación | `e2e_e07_03_missing_strokes_notice` |
| 3 | Dado una animación reproducida, cuando el navegador lo comunica, entonces se guarda `stroke_order_played` | `test_e07_03_stroke_event_accepted` |

- **Derechos:** no aplica.
- **Idioma:** claves `strokes.*`.
- **Guardado:** no aplica.
- **Analítica:** `stroke_order_played`.
- **Datos personales:** no aplica.
- **Fuera de alcance:** descomposición en radicales.

### HU-E07-04 · Avisar de un error
**Como** estudiante **quiero** reportar un fallo desde la ficha o la tarjeta **para** que se corrija.
**Corte:** V1b · **Tipo:** U · **Reglas:** R-CON-14 · **Necesita:** HU-E07-02

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado una palabra, cuando envía un reporte con el elemento que falla y un comentario, entonces queda abierto | `test_e07_04_report_created_open` |
| 2 | Dado un elemento que no existe en la lista, cuando envía el reporte, entonces se rechaza | `test_e07_04_invalid_element_rejected` |
| 3 | Dado un reporte enviado, cuando se registra su evento, entonces lleva el elemento y el nivel, nunca el comentario | `test_e07_04_report_event_has_no_comment` |

- **Derechos:** cualquier estudiante puede reportar.
- **Idioma:** claves `report.*`; el comentario se guarda tal cual.
- **Guardado:** si falla el envío, el formulario conserva lo escrito.
- **Analítica:** `content_report_submitted`.
- **Datos personales:** el comentario es texto libre; al eliminar la cuenta el reporte pierde su vínculo con ella.
- **Fuera de alcance:** conversar con el editor sobre el reporte.
