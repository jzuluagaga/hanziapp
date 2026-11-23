# HanziApp · Backend

API de Django para HanziApp. La documentación de producto vive en `Docs/` (empieza por `Docs/00-indice.md`); el contrato de la API está en `Docs/10-api.md` y las historias con sus pruebas en `Docs/historias/`.

## Arrancar

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py build_system_decks      # mazos del sistema (R-MAZ-02, D-43); repetible
python manage.py runserver               # API en http://127.0.0.1:8000/api/v1/
python manage.py test                    # todas las pruebas
python3 Docs/tools/verificar_docs.py --tests .,../frontend   # documentación y pruebas citadas
```

`DATABASE_URL` elige PostgreSQL (`postgres://…`); sin ella se usa `db.sqlite3`. Otras variables: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `AUDIO_BASE_URL`, `RESEND_API_KEY`, `DRF_NUM_PROXIES`, `SECURE_SSL_REDIRECT`.

## Módulos (Docs/09-arquitectura.md §2)

| App | Qué posee |
|---|---|
| `users` (`accounts`) | Cuentas, acceso, perfil, cohorte, intentos fallidos |
| `languages` | Idiomas e interruptores |
| `content` | Palabras, versiones, validaciones, audio, reportes; lecturas para estudiantes en `content/services/reading.py` |
| `entitlements` | Planes, concesiones, límites, cuotas y freno de costos |
| `decks` | Mazos del sistema |
| `scheduling` | Estados de repaso, historial y adaptador de FSRS (`fsrs` 6.3.3) |
| `study` | Sesiones, colas, respuestas idempotentes y reanudación |
| `progress` | Días, racha, progreso y `GET /today` |
| `privacy` | Política, consentimientos, voz (preparación) y eliminación de cuenta |
| `analytics` | Eventos con esquema cerrado y tablero en `/admin/analytics/` |
| `ops` | Parámetros con valores iniciales, auditoría, `/health` y `/config` |

`vocab` y `users.UserProgress` son del MVP anterior: ya no tienen rutas y solo se conservan por sus datos.

## Tareas programadas

| Comando | Frecuencia | Regla |
|---|---|---|
| `close_days` | Cada hora | R-PRO-09 |
| `expire_sessions` | Diaria | R-SES-08 |
| `purge_voice_recordings` | Diaria | R-DAT-08 |

## Desarrollo con contenido de prueba

`dev_publish_sample --level 1 --level 2` publica borradores **sin revisión** y con audio de marcador para probar el frontend. Solo corre con `DEBUG=True` y una base `*dev.sqlite3` (ver el README del frontend).

---

## Contenido HSK

Tubería de contenido según `Docs/08-contenido.md`. Genera, valida y publica el
contenido de cada palabra del sílabo HSK 2025, con revisión humana obligatoria.
Las reglas viven en `Docs/03-reglas-de-negocio.md` (`R-CON`, `R-IDI`); este
archivo solo explica cómo operar.

## Modelo en dos capas

```
Word (sílabo: hanzi, pinyin, nivel, orden — id estable, R-CON-03)
 ├─ ThirdPartyGloss       glosa de terceros, solo interna (R-CON-02)
 ├─ WordBaseVersion       base: acepciones + ejemplos en chino, común a todos los idiomas
 │    └─ Sense ─ Example  (el pinyin de los ejemplos lo calcula la tubería)
 └─ LanguageContentVersion  por idioma: significados y traducciones de una base
```

Cada capa tiene como máximo un borrador y una versión publicada (R-CON-05). Un
idioma solo se publica sobre su base publicada (R-CON-04). Los idiomas son
filas de `languages.Language`: español activo, inglés cargado e inactivo
(R-IDI-02).

## Recorrido de un nivel

```bash
pip install -r requirements.txt
python manage.py migrate

# 0. (Si la fuente es un PDF "New HSK Vocabulary" de Mandarin Bean) pasarlo a JSON
python manage.py syllabus_from_pdf ~/Downloads/New-HSK-Vocabulary-Level-2.pdf --level 2 --out content_pipeline/hsk2_final.json
#    (corrige erratas conocidas del PDF y falla si el total no coincide con ENTRIES)
# 1. Sílabo (+ glosas de terceros como campo interno)
python manage.py load_syllabus content_pipeline/hsk1_final.json --gloss-source mandarin_bean
# 2. Cotejo contra el documento oficial transcrito (debe dar cero diferencias)
python manage.py check_syllabus <archivo_oficial.json>
# 4. Borradores. Sin opciones es un ensayo (no gasta créditos)
python manage.py generate_drafts --level 1 --language es
python manage.py generate_drafts --level 1 --language es --words 好 只 --sync   # muestra
python manage.py generate_drafts --level 1 --language es --submit               # lote
python manage.py generate_drafts --collect msgbatch_xxx                        # retomar
# 5. Validaciones (también corren al generar y al editar en el panel)
python manage.py validate_drafts --level 1
# 7–8. Revisar, editar y publicar en /admin › Contenido (permiso content.manage_content)
```

Al cargar un nivel nuevo, sus palabras pasan a leerse con su pinyin oficial
también en los ejemplos de los demás niveles:
`python manage.py refresh_pinyin --dry-run` muestra qué cambiaría en los
borradores (lo publicado no se toca) y sin `--dry-run` lo aplica.

Repetir `generate_drafts` no duplica nada: omite las palabras con contenido en
ese idioma y nunca toca lo publicado. `--regenerate` rehace borradores de ese
idioma; `--replace-base-drafts` rehace además bases en borrador importadas o
editadas.

**Añadir inglés** (08-contenido.md §8): `generate_drafts --language en`. Sobre
palabras con base solo genera significados y traducciones, sin acepciones ni
ejemplos nuevos. Después: revisar, publicar y encender el interruptor del
idioma en el panel. Sin migraciones ni código (R-IDI-10).

## Pinyin

El modelo nunca escribe pinyin. `content/pipeline/pinyin.py` lo calcula así:

1. Segmenta con jieba, al que se añaden las palabras del sílabo.
2. Las palabras del sílabo se leen con su **pinyin oficial**, también dentro
   de compuestos. Lo demás se lee con pypinyin ampliado con CC-CEDICT, que sí
   marca el tono neutro (爸爸 bàba).
3. Aplica las excepciones de `content/pipeline/data/pinyin_overrides.json`
   (dato editable), las partículas según su función (的/地/得 de, 着 zhe,
   modal 得 děi, clasificador 只 zhī) y los cambios de tono de 一 y 不.
4. Si una acepción se lee distinto del sílabo (好 hào), `Sense.reading` fija
   esa lectura para la palabra en sus ejemplos.

Contra las 1.023 frases de HSK 1 corregidas a mano, coincide en 957. Las
diferencias restantes siguen el sílabo oficial (学生 xuéshēng, 对不起
duìbuqǐ) o son tonos neutros que el diccionario admite.

## Parámetros

En `ops.Parameter` (panel › Operación), con auditoría:
`content.example_max_chars` y `content.example_level_tolerance` por nivel
(HSK 1–6 propuestos, ver `Docs/03` §11), `content.examples_max_similarity`,
`content.examples_per_sense` y `content.audio_voice`. El modelo de Claude y su
esfuerzo se fijan con `CONTENT_GENERATION_MODEL` (por defecto
`claude-sonnet-5-5`) y `CONTENT_GENERATION_EFFORT` (por defecto `medium`), o
con `--model` / `--effort`. Cada borrador guarda en `generation_meta` el
modelo, el esfuerzo, la versión del prompt y el lote del que salió.

## Pendiente

- **Audio** (`synthesize_audio`): falta elegir proveedor de síntesis y
  verificar sus condiciones (08-contenido.md §1). Hasta entonces
  `audio_present` falla y nada se puede publicar.
- `load_characters` (trazos) y `check_level_ready`.
- Evento de analítica `content_published`: hoy queda en el registro de
  auditoría; falta el módulo `analytics`.

## Contenido anterior

`import_legacy_content` trajo el HSK 1 de la app `vocab` como borradores
`imported`; después HSK 1 se regeneró entero con Sonnet 5.5. La carpeta
`content_pipeline/` es la tubería anterior: se conserva por `hsk1_final.json`,
`hsk2_final.json` … `hsk6_final.json` (fuentes del sílabo y las
glosas) y como referencia, pero su código ya no se usa.

## Pruebas

```bash
python manage.py test content
```
