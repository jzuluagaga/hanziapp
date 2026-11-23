# Tarea 4 · Herramientas del editor, tablero y pruebas de carga

**Rama:** `feat/editor-tablero` · **Dificultad:** media-alta · **Toca:** backend (`content/admin.py`, `analytics`), una herramienta de carga, docs

## Qué hay hoy

- El editor revisa y publica en el **panel de Django** (D-13: no se construye un panel propio). Ya se puede publicar por lote y volver a validar, pero revisar 500 palabras una a una es lento: no hay filtro por validación fallida ni una vista para revisar palabra por palabra.
- El tablero de retención (`/admin/analytics/`, HU-E14-01) solo muestra tablas.
- Faltan las pruebas de carga `load_answer_submit` (Q-01) y `load_dictionary_search` (Q-06).

## Prompt

```text
Eres un desarrollador que se une a HanziApp (backend Django en backend/). Tu tarea es
hacer más rápida la revisión editorial dentro del panel de Django, mejorar el tablero de
retención y escribir las pruebas de carga. Trabaja en la rama feat/editor-tablero y
entrega un pull request.

ANTES DE ESCRIBIR CÓDIGO, lee completos:
- tareas/00-reglas-comunes.md
- backend/Docs/04-decisiones.md: D-12 y D-13 (todo se revisa en el panel de Django; no
  hay panel propio)
- backend/Docs/08-contenido.md §2 a §4 (recorrido de una palabra, validaciones y qué
  comprueba el revisor)
- backend/Docs/03-reglas-de-negocio.md: R-CON-04 a R-CON-07, R-DAT-07, R-DAT-10
- backend/Docs/07-eventos-y-metricas.md §4 (M-01 a M-14)
- backend/Docs/06-calidad.md: Q-01, Q-06, Q-23
- backend/Docs/historias/E13-operar-el-contenido.md y E14-operar-el-producto.md
- Código: backend/content/admin.py, backend/content/services/editorial.py (publish_word
  y publish_base; SOLO LECTURA: publica únicamente a través de estas funciones),
  backend/content/services/validation.py, backend/analytics/metrics.py,
  backend/analytics/views.py, backend/analytics/templates/analytics/dashboard.html

PASO 1. Propuesta (sin código todavía).
Escribe en el pull request, en menos de una página, cómo será la vista de revisión:
qué muestra, qué botones tiene y qué pasa con cada uno. Debe cumplir:
- Vive dentro del admin de Django: una vista personalizada registrada con get_urls() de
  un ModelAdmin, con la plantilla del admin y el permiso content.manage_content.
- Muestra una palabra a la vez: hanzi, pinyin y nivel; acepciones con categoría y
  significado en español; ejemplos con pinyin, traducción y audio; y las validaciones
  con su estado.
- Botones: "Publicar y siguiente" (llama a content.services.editorial.publish_word),
  "Editar" (lleva al formulario actual del borrador) y "Saltar".
- Filtros: nivel, con o sin validaciones fallidas, y código de validación.
- Orden: el del sílabo. Muestra "faltan N por revisar en HSK X".
DETENTE y espera aprobación.

PASO 2. Revisión dentro del admin (backend/content/admin.py y una plantilla en
backend/content/templates/admin/content/).
- Implementa la vista aprobada. Nada se publica sin pasar por publish_word, que ya
  revalida, registra quién publicó y emite el evento: no repliques esa lógica.
- Añade a las listas de WordBaseVersion y LanguageContentVersion un filtro lateral
  "Validación fallida" (por código) y una columna con los códigos fallidos.
- Pruebas en backend/content/tests/test_review_view.py:
  test_review_view_requires_editor, test_review_view_shows_next_unpublished_in_syllabus_order,
  test_review_publish_and_next_uses_editorial_service,
  test_review_cannot_publish_with_failed_validation, test_failed_validation_filter.
  Usa los helpers de content/tests/helpers.py.

PASO 3. Tablero de retención (backend/analytics/).
- Convierte las tablas de dashboard.html en gráficos SVG generados en el servidor, sin
  librerías externas de JavaScript ni CDN (las métricas no salen del servidor, D-41):
  barras de M-02 por cohorte con las líneas del 15 % y el 35 % de la compuerta V1 → V2;
  M-03 por día; y M-04 por tramo y habilidad, con una línea en el 90 %
  (fsrs_target_retention).
- Añade M-01 (activación en 24 h) y M-07 (sesiones completadas ÷ iniciadas) a
  metrics.py, calculadas SOLO con eventos, como las demás.
- Junto a cada métrica, una línea que explique cómo leerla.
- Pruebas en backend/analytics/tests/test_analytics.py: test_m01_activation_24h y
  test_m07_sessions_completed. Las pruebas test_e14_01_* existentes deben seguir pasando.

PASO 4. Pruebas de carga (backend/load/ con Locust).
- load_answer_submit (Q-01): 50 estudiantes que inician sesión de lectura y responden
  sin parar, cada uno con su cuenta. Umbral: p95 de POST /api/v1/answers ≤ 300 ms.
- load_dictionary_search (Q-06): búsquedas por hanzi, pinyin y significado sobre una
  base con las 5.400 palabras. Umbral: p95 de GET /api/v1/words/search ≤ 300 ms.
- Cada escenario es una clase o archivo que contiene el nombre exacto
  (load_answer_submit, load_dictionary_search), para que el verificador lo encuentre.
- Un archivo backend/load/README.md explica cómo crear las cuentas (comando o script
  con datos ficticios, nunca datos reales), cómo correrlo contra local y cómo leer el
  resultado.
- Corre las dos en tu máquina con SQLite y, si puedes, con PostgreSQL en Docker; anota
  los p95 en el pull request. Si no se cumplen, NO optimices el núcleo: reporta qué
  ruta es lenta y con qué consulta (usa django-debug-toolbar o connection.queries en
  local).

PASO 5. Entrega.
- python manage.py test y verificar_docs.py en verde.
- Pull request con capturas de la vista de revisión y del tablero, los p95 medidos y
  cuánto tardaste en revisar 20 palabras con la vista nueva frente a la anterior.

NO HAGAS: un panel de administración fuera de Django (D-13); publicar sin
publish_word; cambios en study/, scheduling/, entitlements/ ni privacy/; librerías de
gráficos por CDN; datos reales de estudiantes en las pruebas de carga.
```

## Cómo se revisa

- [ ] La propuesta de la vista fue aprobada antes del código.
- [ ] Publicar desde la vista nueva usa `publish_word` y deja el registro de auditoría.
- [ ] Una palabra con validación fallida no se puede publicar desde la vista.
- [ ] El tablero no carga nada de fuera y solo muestra agregados por cohorte.
- [ ] Los p95 están medidos y anotados; si no se cumplen, el cuello de botella quedó identificado.
