# Tarea 3 · Calidad: pruebas de extremo a extremo e integración continua

**Rama:** `feat/e2e-ci` · **Dificultad:** alta (por volumen) · **Toca:** frontend (Playwright), backend (un comando de siembra), `.github/workflows/`

## Qué hay hoy

- Las historias citan **23 pruebas `e2e_*`** que no existen. El verificador las lista con `python3 backend/Docs/tools/verificar_docs.py --tests backend,frontend`.
- No hay integración continua: nada comprueba los cambios antes de entrar a `main` (Q-27).
- Para probar se necesita un backend con datos. Hoy solo existe la base que se pasa por privado, que no sirve para la integración continua.

## Prompt

```text
Eres un desarrollador que se une a HanziApp (backend Django en backend/, frontend Next.js 16
en frontend/). Tu tarea es escribir las pruebas de extremo a extremo que piden las
historias y montar la integración continua. Trabaja en la rama feat/e2e-ci y entrega un
pull request (puedes partirlo en dos: primero siembra + CI y después las pruebas).

ANTES DE ESCRIBIR CÓDIGO, lee completos:
- tareas/00-reglas-comunes.md
- backend/Docs/00-indice.md (§4 a §8: cada criterio tiene una prueba con nombre único y
  el verificador lo comprueba)
- backend/Docs/06-calidad.md (Q-03, Q-05, Q-18 a Q-21, Q-25, Q-27, Q-30)
- Todas las historias de backend/Docs/historias/ (cada e2e_* está en un criterio que dice
  exactamente qué comprobar)
- backend/Docs/10-api.md
- frontend/README.md (cómo está conectado: cookies httpOnly, buzón de respuestas)
- backend/hanzi_backend/testing.py (helpers para crear palabras publicadas ficticias)
- frontend/node_modules/next/dist/docs/

PASO 1. Lista de trabajo. Ejecuta
  python3 backend/Docs/tools/verificar_docs.py --tests backend,frontend
y copia en el pull request la lista de pruebas e2e_* que faltan, cada una con el
criterio de su historia. No escribas pruebas que no estén en esa lista ni cambies los
nombres.

PASO 2. Datos de prueba reproducibles (backend).
- Crea backend/content/management/commands/seed_e2e.py: con DEBUG=True y una base
  cuyo nombre termine en e2e.dev.sqlite3 (si no, se niega, como dev_publish_sample),
  crea con los helpers de hanzi_backend/testing.py unas 40 palabras ficticias de HSK 1
  y 10 de HSK 2 publicadas en español, con audio de marcador tts:, arma los mazos
  (build_system_decks) y crea una cuenta e2e@example.com con una contraseña fija.
  Repetible: si ya existe, no duplica.
- No uses datos reales ni glosas de terceros.
- Prueba: backend/content/tests/test_seed_e2e.py con test_seed_e2e_is_idempotent_and_guarded.

PASO 3. Playwright (frontend).
- Instala @playwright/test como dependencia de desarrollo y crea
  frontend/playwright.config.ts. Debe levantar Django (migrate, seed_e2e y runserver
  8001 con DATABASE_URL a una base temporal *e2e.dev.sqlite3) y Next (pnpm build &&
  pnpm start -p 3001 con HANZI_API_URL=http://127.0.0.1:8001) antes de las pruebas.
- Proyectos: chromium, webkit y firefox (Q-21), y un móvil de 360 px (Q-20).
- Pruebas en frontend/e2e/, un archivo por épica (e03-estudiar.spec.ts,
  e06-no-perder-nada.spec.ts, …). Cada test() se llama EXACTAMENTE como la prueba de la
  historia, por ejemplo test("e2e_resume_exact_recognition", …), para que el verificador
  la encuentre.
- Pistas para las difíciles:
  * e2e_next_card_does_not_wait_for_network: con page.route retrasa /api/v1/answers 3 s
    y comprueba que la siguiente tarjeta aparece en menos de 100 ms (Q-03).
  * e2e_e06_01_outbox_survives_reload: context.setOffline(true), responde 2 tarjetas,
    recarga, vuelve la red y comprueba en la API que llegaron exactamente 2 respuestas.
  * e2e_e06_03_rejected_device_relocates: dos contextos con la misma cuenta y la misma
    sesión; responde en uno y luego en el otro.
  * e2e_resume_exact_writing: Hanzi Writer dibuja en un SVG. Simula trazos con
    page.mouse a lo largo de los "medians" del JSON del carácter, o, si no es viable,
    documenta el motivo en el pull request y deja la prueba marcada como test.fixme con
    ese nombre exacto.
  * e2e_study_session_keyboard_only y Q-18: usa @axe-core/playwright para el análisis
    de accesibilidad de registro, acceso, sesión y ficha; cero incumplimientos graves.
- Añade el script "test:e2e": "playwright test" en frontend/package.json.

PASO 4. Integración continua (.github/workflows/ci.yml en la raíz del repositorio).
Trabajos que corren en cada pull request y en cada push a main:
  1. backend: Python 3.12, pip install -r backend/requirements.txt,
     python manage.py test con SECRET_KEY de prueba, y verificar_docs.py
  2. frontend: pnpm install --frozen-lockfile, pnpm typecheck, pnpm test:i18n, pnpm build
  3. auditoría: pip-audit y pnpm audit --audit-level=high (Q-13)
  4. e2e: el trabajo de Playwright, que guarda el informe HTML como artefacto
  5. verificador con --tests backend,frontend. Al principio fallará por las pruebas
     pendientes: márcalo continue-on-error hasta que las tuyas existan y explícalo en el
     pull request.
Usa caché de pip y de pnpm. Ningún secreto real: SECRET_KEY de prueba en el propio
workflow.

PASO 5. Entrega.
- El verificador con --tests ya no lista ninguna e2e_* (salvo las que dejes en fixme
  con su justificación).
- frontend/README.md: cómo correr las pruebas e2e en local.
- Pull request con: lista de pruebas hechas y pendientes, tiempo que tarda la
  integración continua y capturas del informe.

NO HAGAS: cambios en la lógica de la app para que una prueba pase (si encuentras un
error, abre un issue con los pasos para reproducirlo y avisa); pruebas que dependan de
red externa; desactivar pruebas sin dejar la razón escrita.
```

## Cómo se revisa

- [ ] La integración continua corre en el pull request y queda en verde, salvo el verificador marcado como pendiente.
- [ ] Cada nombre `e2e_*` coincide exactamente con el de la historia.
- [ ] `seed_e2e` se niega a correr fuera de una base `*e2e.dev.sqlite3`.
- [ ] Ninguna prueba depende de Google, jsDelivr ni otros servicios externos.
- [ ] Los errores que encontró están en issues, no "arreglados" a escondidas.
