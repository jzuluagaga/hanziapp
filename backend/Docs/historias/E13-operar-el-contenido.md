# E13 · Operar el contenido

**Tope de extensión:** 160 líneas. **Estado:** primera versión (22 nov 2026). Varias pruebas ya existían en `content/tests/` antes de escribir este archivo; se citan con su nombre real.

---

### HU-E13-01 · Cargar el sílabo de un nivel
**Como** editor **quiero** cargar las palabras de un nivel con sus datos del sílabo **para** que existan cotejadas con el documento oficial.
**Corte:** V1a · **Tipo:** O · **Reglas:** R-CON-01, R-CON-03 · **Necesita:** —

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado un archivo del sílabo, cuando se carga dos veces, entonces no se duplica nada y cada palabra conserva su identificador | `test_load_syllabus_is_idempotent_and_keeps_ids` |
| 2 | Dado lo cargado y el documento oficial, cuando se cotejan, entonces se listan las diferencias de conteo, hanzi y pinyin | `test_mismatches` |
| 3 | Dado palabras recién cargadas sin contenido, cuando un estudiante las consulta, entonces las ve "en revisión" con su dato del sílabo | `test_e13_01_loaded_words_visible_in_review` |

- **Derechos:** solo el editor (`content.manage_content`).
- **Idioma:** no aplica; el dato del sílabo es común.
- **Guardado:** el comando es repetible sin efectos dobles.
- **Analítica:** no aplica.
- **Datos personales:** no aplica.
- **Fuera de alcance:** carga desde una pantalla propia (`D-13`).

### HU-E13-02 · Generar borradores validados, con audio
**Como** editor **quiero** que un comando deje borradores, validaciones y audio **para** revisar en lugar de redactar.
**Corte:** V1a · **Tipo:** O · **Reglas:** R-CON-02, R-CON-06, R-CON-07, R-CON-13 · **Necesita:** HU-E13-01

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado palabras sin contenido, cuando se generan, entonces quedan un borrador de base y uno por idioma, con el pinyin de los ejemplos calculado por la tubería | `test_full_mode_creates_base_and_language_drafts_with_computed_pinyin` |
| 2 | Dado una generación ya hecha, cuando se repite, entonces no duplica nada | `test_rerun_does_not_duplicate` |
| 3 | Dado una base publicada, cuando se genera otra vez, entonces nunca se toca | `test_published_base_is_never_regenerated` |
| 4 | Dado un borrador correcto, cuando se valida, entonces pasa todas las validaciones | `test_good_draft_passes_all_validations` |
| 5 | Dado un texto con su voz, cuando se sintetiza dos veces, entonces se genera y se guarda un solo audio | `test_e13_02_synthesize_audio_is_idempotent` |

- **Derechos:** solo el editor.
- **Idioma:** genera para el idioma indicado; el inglés solo traduce bases publicadas.
- **Guardado:** los lotes se retoman sin duplicar (`GenerationJob`).
- **Analítica:** no aplica.
- **Datos personales:** no aplica.
- **Fuera de alcance:** generar desde la interfaz (`D-13`).

### HU-E13-03 · Revisar y publicar
**Como** editor **quiero** revisar, editar y publicar palabra por palabra o por lote **para** que solo llegue contenido revisado.
**Corte:** V1a · **Tipo:** O · **Reglas:** R-CON-04, R-CON-05, R-CON-06, R-CON-07, R-IDI-05 · **Necesita:** HU-E13-02

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado un borrador con una validación fallida, cuando intenta publicarlo, entonces no se puede | `test_cannot_publish_with_failed_validation` |
| 2 | Dado un contenido por idioma, cuando su base no está publicada, entonces no se puede publicar | `test_language_requires_published_base` |
| 3 | Dado una publicación, cuando ocurre, entonces registra quién, cuándo y el origen | `test_publication_records_who_when_origin` |
| 4 | Dado un ejemplo editado en el panel, cuando se guarda, entonces se recalcula su pinyin y se vuelve a validar | `test_editing_example_recomputes_pinyin_and_revalidates` |
| 5 | Dado alguien sin permiso de editor, cuando entra al panel de contenido, entonces no puede publicar | `test_requires_editor_permission` |
| 6 | Dado una publicación, cuando se confirma, entonces se emite `content_published` sin datos del editor | `test_e13_03_publish_emits_event` |

- **Derechos:** solo el editor.
- **Idioma:** cada idioma se publica por separado (`R-IDI-05`).
- **Guardado:** publicar es una sola transacción.
- **Analítica:** `content_published`.
- **Datos personales:** el registro de auditoría guarda al editor; no es un estudiante.
- **Fuera de alcance:** flujo de varios revisores.

### HU-E13-04 · Corregir lo publicado
**Como** editor **quiero** cambiar una palabra publicada **para** corregirla sin que nadie pierda progreso ni vea un estado intermedio.
**Corte:** V1b · **Tipo:** O · **Reglas:** R-CON-05, R-CON-11 · **Necesita:** HU-E13-03

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado una palabra publicada en corrección, cuando se edita el borrador, entonces la versión publicada sigue visible hasta publicar la nueva | `test_correction_keeps_published_visible_and_republishes_languages_together` |
| 2 | Dado estados de repaso de una palabra, cuando se publica su corrección, entonces se conservan | `test_e13_04_correction_keeps_review_states` |
| 3 | Dado una palabra retirada del sílabo, cuando se reconstruyen mazos y colas, entonces sale de ambos y su historial se conserva | `test_e13_04_retired_word_leaves_decks_and_queues` |
| 4 | Dado cualquier capa, cuando se crean versiones, entonces nunca hay más de un borrador y una publicada | `test_at_most_one_draft_and_one_published` |

- **Derechos:** solo el editor.
- **Idioma:** corregir la base republica los idiomas que dependen de ella.
- **Guardado:** publicar la corrección es una sola transacción.
- **Analítica:** `content_published`, `content_unpublished`.
- **Datos personales:** no aplica.
- **Fuera de alcance:** avisar a los estudiantes de la corrección.

### HU-E13-05 · Atender los reportes
**Como** editor **quiero** ver los reportes abiertos y resolverlos o descartarlos **para** corregir lo que falla.
**Corte:** V1b · **Tipo:** O · **Reglas:** R-CON-14, R-DAT-10 · **Necesita:** HU-E07-04

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado reportes de estudiantes, cuando el editor abre el panel, entonces ve los abiertos con la palabra, el elemento y el comentario | `test_e13_05_open_reports_listed_in_admin` |
| 2 | Dado un reporte, cuando se resuelve o descarta con motivo, entonces queda en el registro de auditoría | `test_e13_05_resolution_audited` |
| 3 | Dado un reporte cerrado, cuando se confirma, entonces se emite `content_report_resolved` con el resultado y los días que estuvo abierto | `test_e13_05_resolution_emits_event` |

- **Derechos:** solo el editor.
- **Idioma:** no aplica; el panel de Django está en español.
- **Guardado:** no aplica.
- **Analítica:** `content_report_resolved`.
- **Datos personales:** el comentario del estudiante se ve en el panel; el reporte no muestra su correo.
- **Fuera de alcance:** responder al estudiante.
