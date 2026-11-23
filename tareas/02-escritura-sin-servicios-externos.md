# Tarea 2 · Escritura sin servicios externos

**Rama:** `feat/escritura-trazos` · **Dificultad:** media-alta · **Toca:** backend (`content`, `analytics`), frontend (componentes de escritura), docs

## Qué hay hoy

- La escritura usa **Hanzi Writer 3.7.3** (`frontend/src/components/study/writing-card.tsx` y `frontend/src/components/word/stroke-animation.tsx`).
- Hanzi Writer descarga los datos de trazos de cada carácter desde **jsDelivr**, un servidor externo. Si jsDelivr falla, no se puede escribir, y habría que nombrarlo en la política (R-DAT-11).
- La lista de escritura del sílabo (700 caracteres, R-ESC-10) ya está cargada en `content.Character` (`writing_level`) con `load_writing_list`, y la cola de escritura solo pide esos caracteres. Lo que falta son los **datos de trazos**: el comando `load_characters` no existe (`backend/Docs/08-contenido.md` §2, paso 3). Por eso hoy se ofrecen todos los caracteres, tengan o no datos de trazos (R-CON-12).
- Tampoco existe `check_level_ready` (08-contenido §5), ni un informe para ajustar el umbral de trazos errados (métrica M-10).

## Prompt

```text
Eres un desarrollador que se une a HanziApp (backend Django en backend/, frontend Next.js 16
en frontend/). Tu tarea es que la escritura de caracteres no dependa de servicios
externos y quede medida. Trabaja en la rama feat/escritura-trazos y entrega un pull
request.

ANTES DE ESCRIBIR CÓDIGO, lee completos:
- tareas/00-reglas-comunes.md
- backend/Docs/03-reglas-de-negocio.md: R-CON-12, R-CON-15, R-ESC-01 a R-ESC-08, R-DAT-11
- backend/Docs/08-contenido.md: §1 (fuentes y licencias), §2 (paso 3 load_characters y
  paso 9 check_level_ready) y §5 (cuándo un nivel está listo)
- backend/Docs/07-eventos-y-metricas.md: answer_recorded y M-10
- backend/Docs/historias/E05-escribir-caracteres.md
- Código: backend/content/models.py (Character, con writing_level),
  backend/content/management/commands/load_writing_list.py, backend/content/services/reading.py
  (characters_of, chars_without_strokes), backend/study/queue.py (cómo la cola omite
  caracteres sin trazos; SOLO LECTURA, no lo modifiques),
  backend/content/management/commands/ (imita el estilo de load_syllabus y
  check_syllabus), backend/analytics/metrics.py y su plantilla dashboard.html,
  frontend/src/components/study/writing-card.tsx,
  frontend/src/components/word/stroke-animation.tsx
- La documentación de Hanzi Writer sobre la opción charDataLoader, y el repositorio
  de datos hanzi-writer-data (Make Me a Hanzi).

PASO 1. Licencias (sin código todavía).
Averigua y anota la licencia exacta de los datos de trazos de Make Me a Hanzi y de
hanzi-writer-data, qué obliga (atribución, aviso de licencia y si lo derivado debe
compartirse igual) y desde dónde se descargan. Escríbelo en un comentario del pull
request y actualiza la fila "Datos de trazos" de Docs/08-contenido.md §1.
DETENTE y espera aprobación: si la licencia no permite servir los datos desde nuestra
app, la tarea cambia.

PASO 2. Comando load_characters (backend/content/management/commands/load_characters.py).
- Recibe una carpeta local con los JSON de hanzi-writer-data (un archivo por carácter)
  y una o varias opciones --level.
- Recorre los caracteres de la lista de escritura de esos niveles (Character con
  writing_level) y actualiza has_stroke_data según exista su archivo. NUNCA modifiques
  writing_level ni writing_order: los gestiona load_writing_list.
- Copia SOLO los JSON de esos caracteres a frontend/public/strokes/<carácter>.json
  (con la opción --out, que por defecto apunta ahí). Así no se sube el paquete entero.
- Es repetible: una segunda ejecución no cambia nada si nada cambió. Imprime cuántos
  caracteres tienen datos y lista los que no.
- Pruebas en backend/content/tests/test_characters.py, con una carpeta de JSON
  ficticios creada en un directorio temporal:
  test_load_characters_marks_stroke_data, test_load_characters_is_idempotent,
  test_load_characters_copies_only_needed_files.
- La prueba existente test_e05_01_chars_without_strokes_skipped debe seguir pasando.

PASO 3. Frontend: trazos servidos desde la app.
- En writing-card.tsx y stroke-animation.tsx usa la opción charDataLoader de Hanzi
  Writer para cargar /strokes/<carácter>.json desde nuestro propio dominio, en lugar
  de jsDelivr. Pon la función de carga en un solo archivo (por ejemplo
  frontend/src/lib/strokes.ts) y úsala en los dos componentes.
- Si el archivo no existe, se muestra el aviso que ya existe (session.write.loadError,
  y en la ficha un aviso equivalente por clave de traducción). No se cae la pantalla.
- Añade la atribución y la licencia de los datos a la página /credits (R-CON-15), por
  clave de traducción.

PASO 4. Comando check_level_ready (backend/content/management/commands/check_level_ready.py).
- Uso: python manage.py check_level_ready --level 1 [--language es]
- Informe con las condiciones automatizables de 08-contenido §5:
  * total del sílabo frente a publicadas en el idioma (100 % para estar listo)
  * versiones publicadas sin revisor (published_by vacío) o con validaciones fallidas:
    la consulta de Q-23, que debe dar 0
  * palabras publicadas sin audio de la palabra o de alguno de sus ejemplos
  * caracteres de la lista de escritura del nivel sin datos de trazos
- Termina con "LISTO" y código de salida 0, o "NO LISTO" y código 1, con la lista de lo
  que falta (máximo 20 por categoría y el total).
- Solo lectura: no modifica nada.
- Pruebas en backend/content/tests/test_level_ready.py: test_check_level_ready_reports_missing
  y test_check_level_ready_passes_complete_level. Usa los helpers de
  backend/hanzi_backend/testing.py y content/tests/helpers.py.

PASO 5. Informe del umbral de escritura (M-10).
- En backend/analytics/metrics.py añade writing_report(): usando SOLO eventos
  answer_recorded con skill writing y mode recall, devuelve el porcentaje de "Recordé",
  la distribución de stroke_misses (0, 1, 2, 3, 4 o más) y la comparación con y sin
  pista. Inclúyelo en summary().
- Muéstralo en backend/analytics/templates/analytics/dashboard.html con una tabla.
- Prueba en backend/analytics/tests/test_analytics.py: test_m10_writing_report.

PASO 6. Entrega.
- Actualiza Docs/08-contenido.md §2 (pasos 3 y 9 ya existen) y la sección "Pendiente"
  del backend/README.md.
- python manage.py test, pnpm typecheck, pnpm test:i18n y verificar_docs.py en verde.
- Pull request con: qué hiciste, cómo probarlo (de dónde bajar hanzi-writer-data y el
  comando exacto), y cuántos caracteres de HSK 1 y 2 quedaron sin datos.

NO HAGAS: cambios en backend/study/ ni en la cola; subir hanzi-writer-data completo al
repositorio; cambiar la regla de calificación de escritura (R-ESC-03); textos fuera de
los catálogos.
```

## Cómo se revisa

- [ ] La licencia quedó escrita en `08-contenido.md` y aprobada antes del código.
- [ ] Ya no hay peticiones a jsDelivr: verificar en la pestaña Red del navegador.
- [ ] `load_characters` es repetible y solo copia los caracteres de los niveles pedidos.
- [ ] `check_level_ready` es de solo lectura y su código de salida sirve para la integración continua.
- [ ] El informe M-10 sale solo de eventos.
