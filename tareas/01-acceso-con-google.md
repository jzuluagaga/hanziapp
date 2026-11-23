# Tarea 1 · Acceso con Google (HU-E02-03)

**Rama:** `feat/google-login` · **Dificultad:** alta · **Toca:** backend (`users`), Next (rutas de acceso), frontend (acceso y registro), docs

## Qué hay hoy

- `POST /api/v1/auth/google` (`backend/users/views.py`, `GoogleAuthView`) valida el token de Google y exige correo verificado (R-CTA-07). **Solo funciona si la cuenta ya existe**; si no, responde `google_signup_not_available`.
- No hay registro con Google, ni ruta en Next, ni botón, ni `GOOGLE_CLIENT_ID` configurado.
- HU-E02-03 es de V2 y no tiene historia detallada.

## Qué necesitas fuera del código

Un cliente OAuth propio en Google Cloud Console (APIs y servicios → Credenciales → ID de cliente de OAuth → Aplicación web), con el origen autorizado `http://localhost:3000`. Su ID va en `backend/.env` como `GOOGLE_CLIENT_ID=…` y en `frontend/.env.local` como `NEXT_PUBLIC_GOOGLE_CLIENT_ID=…`. Ninguno de los dos archivos se sube.

## Prompt

```text
Eres un desarrollador que se une a HanziApp (repositorio con backend Django en backend/
y frontend Next.js 16 en frontend/). Tu tarea es implementar el acceso con Google
(historia HU-E02-03). Trabaja en la rama feat/google-login y entrega un pull request.

ANTES DE ESCRIBIR CÓDIGO, lee completos:
- tareas/00-reglas-comunes.md (reglas del equipo: qué no tocar y cómo entregar)
- backend/Docs/00-indice.md (formato de historias y cuándo una historia está lista)
- backend/Docs/03-reglas-de-negocio.md: R-CTA-05, R-CTA-06, R-CTA-07, R-CTA-10,
  R-DAT-01, R-DAT-02, R-DAT-11
- backend/Docs/04-decisiones.md: D-05 y D-31
- backend/Docs/10-api.md (sobre todo §2: Next guarda las credenciales en cookies httpOnly)
- backend/Docs/historias/E02-crear-cuenta-y-empezar.md (imita su formato exacto)
- Código: backend/users/views.py (GoogleAuthView, RegisterView), backend/users/services.py
  (register, login), backend/users/tests.py, frontend/src/app/api/auth/[action]/route.ts,
  frontend/src/lib/server/backend.ts, frontend/src/lib/store/actions.ts (login, register),
  frontend/src/app/login/page.tsx, frontend/src/app/signup/page.tsx
- frontend/node_modules/next/dist/docs/ antes de tocar rutas de Next.

PASO 1. Documentación (sin código todavía).
a) En backend/Docs/05-mapa-de-historias.md cambia la versión de HU-E02-03 de V2 a V1b, y
   en backend/Docs/04-decisiones.md añade la decisión D-45: "Se adelanta el acceso con
   Google a V1b", con estado Propuesta y un porqué de una línea.
b) Detalla HU-E02-03 en backend/Docs/historias/E02-crear-cuenta-y-empezar.md con el mismo
   formato que HU-E02-01: Como/quiero/para; Corte, Tipo, Reglas y Necesita; tabla de
   criterios "Dado… cuando… entonces…", cada uno con una prueba de nombre único; y las
   cinco declaraciones (Derechos, Idioma, Guardado, Analítica, Datos personales) más
   "Fuera de alcance". Criterios mínimos:
   1. Correo verificado por Google que coincide con una cuenta existente → accede
      (test_e02_03_links_existing_verified_account)
   2. Correo no verificado por Google → se rechaza (test_e02_03_unverified_email_rejected)
   3. Token inválido, vencido o emitido para otro cliente → se rechaza
      (test_e02_03_invalid_token_rejected)
   4. Correo nuevo → no se crea la cuenta hasta aceptar la política vigente y declarar la
      mayoría de edad (test_e02_03_new_account_requires_policy_and_adult)
   5. Cuenta nueva por Google → queda igual que una por correo: perfil, concesión Free,
      aceptación de política y un consentimiento por finalidad; además, correo verificado
      y sin contraseña utilizable (test_e02_03_new_account_like_email_signup)
   6. Con signup_mode cerrado no se crean cuentas nuevas por Google
      (test_e02_03_signup_closed_blocks_new_accounts)
   7. Botón de Google en /login y /signup que termina en /today
      (e2e_e02_03_google_button_signs_in)
   Analítica: los eventos login_succeeded (method google), account_registered y
   policy_accepted, que ya están en el catálogo (Docs/07-eventos-y-metricas.md).
c) Ejecuta `python3 backend/Docs/tools/verificar_docs.py`: debe decir "Sin errores".

DETENTE aquí. Muéstrame la historia y espera aprobación antes del paso 2.

PASO 2. Backend (solo en backend/users/; no toques study/, scheduling/, entitlements/,
privacy/ ni migraciones de otras apps).
- Extiende POST /api/v1/auth/google:
  * Cuenta existente con ese correo: igual que hoy (tokens + login_succeeded).
  * Sin cuenta y sin policy_version ni is_adult en el cuerpo: responde 409
    {"error": "google_consent_required", "detail": {"email": "<correo de Google>"}}.
  * Sin cuenta y con policy_version, is_adult (y opcionalmente reminder_consent y
    timezone): crea la cuenta. Extrae de users.services.register una función común
    (por ejemplo _create_account) que usen los dos caminos: no dupliques la lógica de
    política, mayoría de edad, signup_mode, perfil, señal account_created y eventos.
    Luego set_unusable_password() y email_verified_at = ahora.
- Los errores son claves de traducción (R-IDI-03), nunca textos.
- No guardes el token de Google en ningún lado.
- Pruebas en backend/users/tests.py con los nombres del paso 1. Simula
  google.oauth2.id_token.verify_oauth2_token con unittest.mock: ninguna prueba llama a
  Google. Usa override_settings(GOOGLE_CLIENT_ID="test") donde haga falta.
- Actualiza la fila de /auth/google en backend/Docs/10-api.md §4 (qué recibe, qué
  devuelve y sus errores).

PASO 3. Frontend.
- En frontend/src/app/api/auth/[action]/route.ts acepta la acción "google": reenvía a
  Django /api/v1/auth/google y, si responde 200 o 201, guarda las cookies igual que
  login. Si responde 409, devuelve el 409 tal cual.
- Añade en frontend/src/lib/store/actions.ts una acción loginWithGoogle(idToken,
  consent?) que siga el patrón de login() y devuelva AuthResult. Si el resultado es
  google_consent_required, lo devuelve con el correo.
- Componente de botón con Google Identity Services
  (https://accounts.google.com/gsi/client), cargando NEXT_PUBLIC_GOOGLE_CLIENT_ID. Si la
  variable no existe, el botón no se muestra.
- Si la respuesta es google_consent_required, muestra las mismas casillas que /signup
  (política con enlace, mayoría de edad y recordatorio opcional desmarcado) y reenvía el
  mismo id_token con esos datos y la zona horaria del navegador.
- Todos los textos van en es.ts y en.ts; `pnpm test:i18n` debe pasar.

PASO 4. Entrega.
- En la sección de proveedores de la página /data-policy (frontend/src/app/data-policy)
  añade a Google como proveedor de acceso (R-DAT-11), por clave de traducción.
- Verifica que todo pasa: python manage.py test, pnpm typecheck, pnpm test:i18n y
  verificar_docs.py.
- Abre el pull request con: qué hiciste, cómo probarlo en local (incluido cómo crear el
  cliente OAuth) y qué quedó pendiente (por ejemplo, la prueba e2e si no la escribiste).

NO HAGAS: commits a main, guardar o registrar el id_token, cambiar el flujo de
login/registro por correo salvo para extraer la función común, ni usar otra base que
db.equipo.dev.sqlite3.
```

## Cómo se revisa

- [ ] La historia pasa el verificador y fue aprobada antes del código.
- [ ] Las 6 pruebas `test_e02_03_*` existen y pasan, y ninguna llama a Google.
- [ ] El registro por correo y el de Google comparten una sola función.
- [ ] Un usuario nuevo por Google no entra sin aceptar la política.
- [ ] No hay textos fuera de los catálogos.
