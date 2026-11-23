# Reglas comunes para las 4 tareas

Léelas antes de empezar. Tu asistente de IA también debe leerlas: cada prompt empieza pidiéndoselo.

## Preparar el entorno

```bash
git clone https://github.com/jzuluagaga/hanziapp.git && cd hanziapp

# Backend
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp /ruta/donde/guardaste/db.equipo.dev.sqlite3 .      # te la pasa Juan Pablo por privado
echo "SECRET_KEY=dev-solo-local
DEBUG=True" > .env
export DATABASE_URL=sqlite:///$PWD/db.equipo.dev.sqlite3
python manage.py migrate
python manage.py test                                  # deben pasar todas
python manage.py runserver 8000

# Frontend (otra terminal)
cd frontend
pnpm install
HANZI_API_URL=http://127.0.0.1:8000 pnpm dev          # http://localhost:3000
```

La base `db.equipo.dev.sqlite3` trae HSK 1 y 2 publicados **solo para desarrollo** (sin revisión y con audio de marcador `tts:`). No tiene cuentas: crea la tuya en `/signup`.

## Antes de escribir código

1. `backend/Docs/00-indice.md`: convenciones, identificadores y cuándo una historia está terminada.
2. Las reglas (`R-…`), decisiones (`D-…`) e historias que cita tu tarea. **Las reglas mandan:** si el código y `Docs/` no coinciden, gana `Docs/`.
3. `backend/Docs/10-api.md`, si tocas la API.
4. El frontend usa **Next 16**: antes de escribir rutas o páginas, lee `frontend/node_modules/next/dist/docs/`, porque cambió respecto a versiones anteriores.

## Cómo se trabaja

- Una rama por tarea (el nombre está en tu prompt) y **un pull request contra `main`**. Nadie hace commits directos a `main`.
- Commits pequeños con mensajes en español que digan qué y por qué.
- Todo texto visible va en `frontend/src/lib/i18n/es.ts` **y** en `en.ts` (R-IDI-03, R-IDI-04). El servidor devuelve claves de error, nunca textos.
- Cada criterio de aceptación tiene una prueba con el nombre exacto que dice la historia o tu prompt.
- Si tu tarea tiene un punto de **"DETENTE"**, para ahí y espera la aprobación antes de seguir.

## Lo que no se toca sin permiso

Si necesitas cambiar algo de esto, pregúntalo antes:

- `backend/study/`, `backend/scheduling/`, `backend/entitlements/`, `backend/privacy/`: el núcleo (guardado, FSRS, derechos y borrado de cuentas).
- `frontend/src/lib/store/` y `frontend/src/app/api/`: la caché, el buzón de respuestas y las credenciales.
- Migraciones de apps que no son de tu tarea.
- `db.sqlite3` o cualquier base que no sea tu copia `db.equipo.dev.sqlite3`.
- **Nunca** subas `.env`, bases de datos, claves ni archivos de terceros sin licencia clara. El repositorio es público.

## Antes de pedir revisión

```bash
cd backend && python manage.py test && python3 Docs/tools/verificar_docs.py
cd ../frontend && pnpm typecheck && pnpm test:i18n
```

Todo en verde, o explica en el pull request qué falla y por qué. La descripción del pull request debe decir:

1. Qué hiciste y qué historia, regla o requisito cubre.
2. Cómo probarlo en local, paso a paso.
3. Qué quedó pendiente o qué decisiones tomaste por tu cuenta.
