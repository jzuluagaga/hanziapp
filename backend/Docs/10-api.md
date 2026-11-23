# 10 · Contrato de la API

**Para qué sirve:** fija qué rutas expone el servidor, qué reciben, qué devuelven y cómo se comportan ante errores. El frontend y el backend se construyen contra este archivo; si una ruta cambia, cambia aquí primero. Las reglas se citan por ID y viven en `03-reglas-de-negocio.md`.

**Tope de extensión:** 260 líneas. **Estado:** primera versión (22 nov 2026).

---

## 1. Convenciones

| Tema | Regla |
|---|---|
| Prefijo | Todas las rutas cuelgan de `/api/v1/`. Las rutas heredadas (`/api/words`, `/api/decks`, `/api/token`) quedan retiradas |
| Formato | JSON en UTF-8. Fechas-hora en ISO 8601 con zona (UTC); días locales como `YYYY-MM-DD` (`R-PRO-01`) |
| Identificadores | Se envían como texto (`"123"`), también los numéricos, para que el frontend no dependa del tipo de la base |
| Acceso | `Authorization: Bearer <access>`. El navegador **nunca** ve la credencial: la guarda una ruta de servidor de Next en cookie httpOnly y reenvía las peticiones (`Q-11`, sección 2) |
| Errores | `{"error": "<clave>", "detail": {...}}`. La clave es una clave de traducción del catálogo de interfaz (`R-IDI-03`); el servidor nunca devuelve textos para el usuario |
| Cabeceras del cliente | `X-Client: mobile_web` o `desktop_web` y `X-App-Version`, que pasan a los eventos (`07-eventos-y-metricas.md`, sección 1) |
| Política pendiente | Si hay una versión nueva de la política sin aceptar, toda ruta de estudio responde `428 {"error": "policy_required"}` hasta aceptarla (`R-DAT-01`) |

Claves de error comunes: `not_authenticated` (401), `invalid_input` (400, con `detail` por campo), `not_found` (404), `forbidden` (403), `rate_limited` (429).

## 2. Acceso a través de Next

```
Navegador ──▶ /api/auth/{login,register,logout}   (Next) ──▶ /api/v1/auth/…  (Django)
          ──▶ /api/v1/<ruta>                      (Next) ──▶ /api/v1/<ruta>   (Django)
```

- `login` y `register` reciben las credenciales de Django, guardan `access` y `refresh` en cookies `httpOnly`, `Secure` (en producción) y `SameSite=Lax`, y devuelven solo `{ "ok": true }`.
- El reenvío añade `Authorization` desde la cookie y `X-Forwarded-For` con la dirección del estudiante; Django la lee con `DRF_NUM_PROXIES` para limitar peticiones por persona y no por servidor (`Q-12`). Si Django responde 401 y hay `refresh`, renueva una vez y repite la petición.
- `logout` borra las dos cookies.

## 3. Rutas públicas

| Método y ruta | Recibe | Devuelve |
|---|---|---|
| `GET /health` | — | `{status: "ok"}` si la base responde; 503 si no (`Q-08`) |
| `GET /config` | — | `{languages: [{code, is_study_active, is_ui_active}], policy_version, signup_mode, limits: {new_limit_recognition: {min, max, default}, new_limit_writing: {…}}}` |

## 4. Cuenta

| Método y ruta | Recibe | Devuelve | Errores |
|---|---|---|---|
| `POST /auth/register` | `name, email, password, policy_version, is_adult, reminder_consent, cohort?, timezone?` | 201 `{access, refresh}` | `signup_closed` (403), `policy_not_accepted`, `adult_required`, `email_taken`, `weak_password` (400) |
| `POST /auth/login` | `email, password` | `{access, refresh}` | `invalid_credentials` (401), `account_locked` (423), `account_suspended` (403) |
| `POST /auth/refresh` | `refresh` | `{access, refresh}` | `not_authenticated` |
| `POST /auth/password-reset` | `email` | 200 siempre, sin revelar si existe | `rate_limited` |
| `POST /auth/password-reset/confirm` | `uid, token, new_password` | 200 | `reset_link_invalid` |
| `GET /me` | — | Ver abajo | — |
| `PATCH /me/profile` | Cualquier campo de `profile` | `profile` | `language_inactive`, `limit_out_of_range`, `timezone_invalid` |
| `POST /me/policy/accept` | `version` | `policy` | `policy_version_mismatch` |
| `PUT /me/consents/<purpose>` | `granted` | `consents` | `consent_required` (no se puede retirar `general`) |
| `DELETE /me` | `password` | 204 | `invalid_credentials` |

```json
GET /me
{
  "account": {"id": "7", "email": "ana@ejemplo.co", "email_verified": false, "cohort": "confucio-2026a", "created_at": "…"},
  "profile": {"name": "Ana", "ui_language": "es", "study_language": "es", "timezone": "America/Bogota",
              "new_limit_recognition": 10, "new_limit_writing": 5, "theme": "system"},
  "plan": "free",
  "entitlements": {"levels": [1, 2], "own_decks_max": 10},
  "consents": {"general": true, "reminder_email": false, "voice_recording": false},
  "policy": {"current": "2026-11", "accepted": "2026-11", "accepted_at": "…", "required": false},
  "today": "2026-11-22"
}
```

`plan` es el nombre comercial de la concesión de mayor alcance; la interfaz usa `entitlements` para mostrar candados, pero quien decide es el servidor (`R-DER-01`).

## 5. Catálogo

| Método y ruta | Devuelve |
|---|---|
| `GET /levels` | `[{level, total, published, locked, unlocking_plan, decks}]` (`R-CON-16`, `R-DER-11`) |
| `GET /decks?level=N` | `[{id, kind, level, index, size, published, locked, unlocking_plan, counts}]` |
| `GET /decks/<id>` | `{deck, words: [{id, hanzi, pinyin, meaning, editorial, badge}]}`. Emite `deck_viewed` |
| `GET /words?level=N` | `[{id, hanzi, pinyin, level, meaning, editorial}]` de todo el nivel, en el orden del sílabo |
| `GET /words/search?q=` | `[{id, hanzi, pinyin, level, meaning, editorial}]`, máximo 50. Emite `search_performed` sin el texto (`R-IDI-07`) |
| `GET /words/<id>?from=search\|deck\|card` | Ficha. Emite `word_viewed` |
| `POST /words/<id>/reports` | Recibe `element, comment`; devuelve 201. Emite `content_report_submitted` |

`counts` es `{recognition: {due, new}, listening: {due, new}, writing: {due, new}}` para la cuenta, sin contar lo bloqueado ni lo que está en revisión. `badge` es `in_review`, `new`, `due`, `learned` o `scheduled`. `editorial` es `published` o `in_review`.

**Ficha de una palabra** (la misma forma va dentro de las tarjetas):

```json
{"id": "101", "hanzi": "好", "pinyin": "hǎo", "level": 1, "order": 41, "editorial": "published",
 "senses": [{"pos": "adj", "meaning": "bueno; bien", "reading": ""}],
 "examples": [{"zh": "你好！", "pinyin": "Nǐ hǎo!", "translation": "¡Hola!", "audio": null}],
 "characters": ["好"], "audio": "https://…/zh/voz/abc.mp3"}
```

Si la palabra no está publicada en el idioma de estudio, `editorial` es `in_review` y `senses`, `examples` y `audio` vienen vacíos: solo hay dato del sílabo (`R-CON-08`). La glosa de terceros nunca aparece (`R-CON-02`). En desarrollo, un `audio` que empieza por `tts:` indica que no hay archivo y que el navegador debe sintetizarlo; en producción no existe.

## 6. Estudio

| Método y ruta | Recibe | Devuelve |
|---|---|---|
| `GET /today` | — | `{today, counts, active_sessions, streak: {current, max, today_active}, recent_decks: [{id, level, index, sample, recognition: {due, new}}], days: [{day, status}]}` (últimos 14 días cerrados). Cierra antes los días pendientes (`R-PRO-09`) y emite `home_viewed` |
| `POST /sessions` | `scope: {type: "all_due"} \| {type: "deck", deck_id}`, `skill`, `chain?`, `force?` | 201 `{session}`; 200 `{session: null, empty_reason}` (`R-SES-10`); 409 `{error: "session_exists", session}` (`R-SES-05`). Con `force` descarta la existente y crea otra |
| `GET /sessions?status=active` | — | `[resumen]` |
| `GET /sessions/<id>` | — | `{session}` sin efectos |
| `POST /sessions/<id>/resume` | `same_client?` | `{session}` tras saltar lo ya repasado (`R-SES-06`); emite `session_resumed` |
| `POST /sessions/<id>/discard` | — | `{session}` (`R-SES-08`) |
| `POST /answers` | Ver abajo | Ver abajo |

**Sesión**

```json
{"id": "9b1c…", "scope": {"type": "deck", "deck_id": "3", "level": 1, "index": 3}, "skill": "recognition", "kind": "scheduled",
 "status": "active", "chain": true, "position": 4, "started_at": "…",
 "cards": [{"position": 0, "unit": "101", "unit_kind": "word", "word_id": "101", "is_new": false,
            "is_reinforcement": false, "result": "pass", "choices": null}],
 "words": {"101": {…ficha…}},
 "summary": {"answered": 4, "passed": 3, "failed": 1}}
```

`result` es `pass`, `fail`, `skipped` o `null`. En escucha, `choices` trae cuatro identificadores de palabra (la correcta y tres del mismo nivel) en orden fijo (`HU-E04-02`). En escritura, `unit` es el carácter.

**Respuesta** (`R-SES-03`, `R-SES-11`, flujo 1 de `09-arquitectura.md`)

| Campo | Contenido |
|---|---|
| `client_id` | UUID generado en el dispositivo; único por cuenta |
| `session_id`, `position`, `unit` | Tarjeta que se responde. Si en esa posición no está esa unidad sin responder, se rechaza |
| `grade` | `pass` o `fail`. En escucha y escritura de memoria el servidor lo **recalcula** y manda el suyo |
| `choice` | Solo escucha: palabra elegida |
| `writing` | Solo escritura: `{mode: "guided" \| "recall", stroke_misses, hint_used}` (`R-ESC-03`, `R-ESC-04`) |
| `answered_at`, `response_ms`, `replays` | Hora del dispositivo, tiempo de respuesta, repeticiones del audio |
| `attempts`, `first_attempt_at` | Reintentos del buzón, para `answer_delivery_delayed` |

Devuelve 200 `{answer: {client_id, grade, counted, introduced_new}, session: {status, position, cards_added}}`. `cards_added` son los refuerzos insertados (`R-REP-05`), con su posición, para que el dispositivo aplique el mismo cambio. Reenviar el mismo `client_id` devuelve exactamente la misma respuesta. Si la tarjeta ya estaba respondida o no coincide: 409 `{error: "stale_card", session}` con la sesión completa para reubicarse (`R-SES-07`).

## 7. Progreso y eventos

| Método y ruta | Recibe | Devuelve |
|---|---|---|
| `GET /progress` | — | `{learned_words, learned_chars, total_answers, levels: [{level, total, published, learned}], streak: {current, max, today_active}, days: [{day, status}]}`. Emite `progress_viewed` |
| `POST /events` | `name, props` | 202. Solo eventos que nacen en el navegador: `audio_played`, `audio_failed`, `stroke_order_played`, `writing_hint_shown`, `writing_char_abandoned`. Cualquier otro: 400 `event_not_allowed` |

## 8. Lo que no está en V1

Mazos propios, repaso libre, deshacer, meta de examen, invitado, exportación de datos y cobro tienen su lugar en el modelo, pero no tienen ruta hasta su versión (`05-mapa-de-historias.md`, sección 5). Google (`POST /auth/google`) se conserva del código anterior y se activa en V2 (`HU-E02-03`).
