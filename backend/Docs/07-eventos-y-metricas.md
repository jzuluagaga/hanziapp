# 07 · Eventos y métricas

**Para qué sirve:** es el catálogo cerrado de eventos de analítica y la definición exacta de las métricas que se calculan con ellos. Una historia solo puede emitir eventos que estén aquí; si necesita otro, primero se agrega aquí.

**Tope de extensión:** 180 líneas. **Estado:** segunda versión (22 nov 2026); retira los eventos de "Ya la sé".

**Convenciones**

- El nombre del evento es su ID: minúsculas, en inglés, `objeto_acción` en pasado.
- ID de métrica: `M-nn`. No se reutiliza.
- Un evento se escribe en la misma transacción que el hecho que mide (`09-arquitectura.md`, sección 7). Si el hecho no ocurre, el evento no existe.
- Cada evento tiene un esquema cerrado: un campo no declarado aquí hace fallar `test_event_schemas_have_no_pii` (`Q-14`).
- Los eventos se guardan en una tabla propia de PostgreSQL. No se envían a terceros.

---

## 1. Campos comunes

Todo evento los lleva, además de los suyos.

| Campo | Contenido |
|---|---|
| `event_id` | Identificador único del evento |
| `occurred_at` | Instante en UTC |
| `account_key` | Seudónimo estable de la cuenta. No es el identificador de la cuenta ni se deriva del correo (`R-DAT-07`). Vacío en eventos sin cuenta |
| `cohort` | Cohorte de la cuenta, o vacío (`R-CTA-10`) |
| `ui_language`, `study_language` | Idiomas de la cuenta (`R-IDI-13`) |
| `plan` | Plan vigente de la cuenta |
| `local_day` | Día del estudiante al que pertenece el evento (`R-PRO-01`) |
| `client` | `mobile_web` o `desktop_web` |
| `app_version` | Versión desplegada |

**Nunca** van en un evento: nombre, correo, texto escrito por el usuario (ni siquiera la consulta de búsqueda), dirección de red, audio.

Al eliminar una cuenta, su `account_key` se sustituye por un valor aleatorio sin relación con ella, de modo que los conteos históricos se conservan y el vínculo desaparece (`R-DAT-06`).

## 2. Catálogo de eventos de V1

### Cuenta y datos

| Evento | Cuándo | Campos propios | Historia |
|---|---|---|---|
| `account_registered` | Se crea la cuenta | `has_cohort` | HU-E02-01 |
| `login_succeeded` | Acceso correcto | `method` | HU-E02-02 |
| `login_failed` | Acceso rechazado (sin `account_key`) | `reason`: `bad_credentials`, `locked`, `suspended` | HU-E02-02 |
| `password_reset_completed` | Se fija una contraseña nueva | — | HU-E02-02 |
| `policy_accepted` | Se acepta una versión de la política | `policy_version` | HU-E02-01, HU-E10-02 |
| `consent_changed` | Se da o se retira un consentimiento | `purpose`, `granted` | HU-E10-02 |
| `profile_updated` | Se guarda el perfil | `fields` (nombres de campo, sin valores) | HU-E10-01 |
| `account_deleted` | Se elimina la cuenta | `days_since_signup` | HU-E10-03 |

### Estudio

| Evento | Cuándo | Campos propios | Historia |
|---|---|---|---|
| `home_viewed` | Se abre "Hoy" | `due_recognition`, `due_listening`, `due_writing`, `new_available` | HU-E03-01 |
| `session_started` | Se crea una sesión | `session_id`, `skill`, `scope`, `kind`, `queue_size`, `due_count`, `new_count` | HU-E03-01 |
| `session_empty` | Se pide una sesión y no hay nada | `skill`, `reason`: `nothing_due`, `new_limit_reached`, `in_review`, `locked` | HU-E03-01 |
| `answer_recorded` | El servidor confirma una respuesta | Ver tabla siguiente | HU-E03-02, HU-E04-02, HU-E05-02 |
| `new_limit_reached` | Se agota el límite diario de nuevas | `skill`, `limit` | HU-E03-03 |
| `session_completed` | Se responde la última tarjeta | `session_id`, `skill`, `kind`, `answered`, `passed`, `failed`, `duration_s` | HU-E03-04 |
| `session_resumed` | Se reanuda una sesión | `session_id`, `skill`, `position`, `skipped_already_reviewed`, `hours_since_last_answer`, `same_client` | HU-E06-02 |
| `session_discarded` | El estudiante la descarta | `session_id`, `skill`, `position`, `queue_size` | HU-E06-02 |
| `session_expired` | Caduca por inactividad | `session_id`, `skill`, `position`, `queue_size` | HU-E06-02 |
| `answer_delivery_delayed` | Una respuesta se confirmó tras reintentos | `attempts`, `delay_s` | HU-E06-01 |
| `answer_rejected_stale` | Se rechaza una respuesta a una tarjeta ya respondida | `session_id` | HU-E06-03 |
| `audio_played` | Se reproduce un audio | `context`: `card`, `word_page`; `target`: `word`, `example`; `auto` | HU-E04-01 |
| `audio_failed` | Un audio no carga | `context`, `target` | HU-E04-01 |
| `writing_hint_shown` | Se muestra una pista | `auto` | HU-E05-03 |
| `writing_char_abandoned` | Se sale a mitad de un carácter | `strokes_done`, `mode` | HU-E05-02 |

**Campos de `answer_recorded`**

| Campo | Contenido |
|---|---|
| `session_id`, `skill`, `session_kind` | De la sesión |
| `item_kind`, `hsk_level` | `word` o `character`; nivel de la palabra de contexto |
| `grade` | `pass` o `fail` |
| `counted` | Si cambió el estado de repaso (`R-REP-05`, `R-REP-10`, `R-ESC-02`) |
| `is_first_ever` | Primera respuesta de esa tarjeta en esa habilidad |
| `is_reinforcement` | Reaparición tras un fallo en la misma sesión |
| `days_since_last`, `scheduled_days` | Días reales desde el repaso anterior e intervalo que estaba programado |
| `response_ms` | Tiempo entre mostrar la tarjeta y responder |
| Solo escritura | `mode`, `stroke_misses`, `hint_used`, `threshold` (`R-ESC-04`) |
| Solo escucha | `replays` |

### Explorar y organizar

| Evento | Cuándo | Campos propios | Historia |
|---|---|---|---|
| `search_performed` | Se muestra un resultado de búsqueda | `query_kind`: `hanzi`, `pinyin`, `meaning`; `result_count` | HU-E07-01 |
| `word_viewed` | Se abre una ficha | `hsk_level`, `editorial`: `published`, `in_review`; `from`: `search`, `deck`, `card` | HU-E07-02 |
| `stroke_order_played` | Se reproduce una animación de trazos | — | HU-E07-03 |
| `content_report_submitted` | Se envía un reporte | `element`, `hsk_level` | HU-E07-04 |
| `deck_viewed` | Se abre un mazo | `deck_kind`, `hsk_level` | HU-E08-01 |

### Progreso y derechos

| Evento | Cuándo | Campos propios | Historia |
|---|---|---|---|
| `progress_viewed` | Se abre "Progreso" | — | HU-E09-01 |
| `day_closed` | Se fija el estado de un día (`R-PRO-09`) | `status`: `active`, `exempt`, `missed`; `due_at_close` | HU-E09-02 |
| `streak_changed` | La racha crece o se rompe | `length`, `change`: `extended`, `broken` | HU-E09-02 |
| `entitlement_denied` | El motor de derechos niega algo | `capability`, `surface` | HU-E11-01 |

### Operación (emitidos por el editor; sin `account_key` de estudiante)

| Evento | Cuándo | Campos propios | Historia |
|---|---|---|---|
| `content_published` | Se publica una versión | `layer`: `base`, `language`; `language`, `origin`, `hsk_level`, `replaces_published` | HU-E13-03, HU-E13-04 |
| `content_unpublished` | Se retira una versión publicada | `layer`, `language`, `hsk_level` | HU-E13-04 |
| `content_report_resolved` | Se cierra un reporte | `outcome`: `fixed`, `dismissed`; `days_open` | HU-E13-05 |

## 3. Eventos reservados

Están definidos para que el esquema no cambie después, pero nada los emite en V1.

| Evento | Versión | Campos propios |
|---|---|---|
| `guest_started`, `guest_converted` | V2 | `answers_before_signup` |
| `answer_undone` | V2 | `session_id`, `skill` |
| `paywall_viewed` | V2 | `capability`, `surface` |
| `purchase_completed`, `grant_expired` | V3 | `product`, `duration_days` |
| `reminder_sent` | V3 | — |
| `quota_consumed` | V4 | `capability`, `units`, `result`: `ok`, `reverted` |
| `feature_paused_by_budget` | V4 | `capability` |
| `voice_recording_stored` | V4 | `duration_ms` (sin audio ni transcripción) |
| `voice_recording_deleted` | V4 | `reason`: `user`, `retention`, `revocation` |

**Retirados.** `new_word_decided` y el campo `declared_known` de `answer_recorded` desaparecen con "Ya la sé" (D-42). Sus nombres no se reutilizan.

## 4. Métricas

Se calculan por cohorte y por semana de registro. "Activado" significa cuenta con al menos una respuesta contada.

| ID | Métrica | Definición exacta | Para qué |
|---|---|---|---|
| M-01 | Activación | Cuentas con una respuesta contada en las 24 h siguientes al registro ÷ cuentas registradas | Saber si el arranque funciona |
| M-02 | **Retención en la semana 4** | Activados con al menos un día activo entre el día 22 y el 28 desde su registro ÷ activados | **Es la métrica de la compuerta V1 → V2** |
| M-03 | Retención a 1, 7 y 28 días | Activados con día activo exactamente el día N ÷ activados | Forma de la curva |
| M-04 | **Retención real por intervalo** | Respuestas `pass` ÷ respuestas contadas, sin refuerzos, agrupadas por `scheduled_days` (1, 2–6, 7–20, 21 o más) y por habilidad | **Mide si aprenden.** Debe acercarse a `fsrs_target_retention` |
| M-05 | Días activos por semana | Media de días activos por activado en cada semana | Intensidad del hábito |
| M-06 | Carga diaria | Mediana y percentil 90 de respuestas contadas por día activo, por habilidad | Detectar fatiga |
| M-07 | Sesiones completadas | `session_completed` ÷ `session_started`, por habilidad | Tamaño de sesión adecuado |
| M-08 | Reanudación | `session_resumed` ÷ sesiones que quedaron a medias al menos 10 minutos | Si la reanudación resuelve el abandono |
| M-09 | Entregas demoradas | `answer_delivery_delayed` ÷ `answer_recorded`, y su `delay_s` | Salud del guardado; las pérdidas deben ser cero (`Q-02`) |
| M-10 | Escritura | Proporción de `pass` de memoria y distribución de `stroke_misses`, con y sin pista | Ajustar `writing_max_stroke_misses` |
| M-11 | **Retirada** (D-42) | Medía la fiabilidad de "Ya la sé" | — |
| M-12 | Brecha entre lectura y escucha | M-04 de escucha menos M-04 de lectura, mismas palabras | Saber si la escucha aporta |
| M-13 | Errores de contenido | Reportes con `outcome = fixed` por cada 1.000 palabras publicadas, por nivel (`Q-24`) | Calidad editorial |
| M-14 | Reparto de días | Proporción de días activos, exentos y fallados | Comprobar el efecto de `R-PRO-03` |

**Umbrales de decisión.** Solo M-02 tiene umbral fijado (35 % seguir, 15 % parar; `05-mapa-de-historias.md`, sección 1). Los demás se observan durante V1 antes de fijarles uno.

**Límite de lectura.** Con una o dos clases, cada cohorte tendrá unas decenas de cuentas: sirve para decidir seguir o parar, no para comparar variantes pequeñas.

## 5. Conservación

| Dato | Plazo |
|---|---|
| Eventos con `account_key` | 24 meses; después se agregan por cohorte y semana y se borran |
| Eventos de una cuenta eliminada | Se desvinculan en el momento (sección 1) |
| Respuestas y estados de repaso | Mientras exista la cuenta: son datos del producto, no analítica |

El plazo de 24 meses es una propuesta mía y debe figurar en la política de datos.
