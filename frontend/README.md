# HanziApp · Frontend

Pantallas del estudiante de **V1a y V1b**, conectadas a la API de Django (`../backend`). El contrato está en `../backend/Docs/10-api.md` y las historias en `../backend/Docs/historias/`.

## Arrancar

```bash
pnpm install
HANZI_API_URL=http://127.0.0.1:8000 pnpm dev   # http://localhost:3000
pnpm typecheck
pnpm test:i18n      # catálogos completos y sin textos fuera de ellos (R-IDI-03, R-IDI-04)
pnpm build
```

`HANZI_API_URL` es la dirección de Django **vista desde el servidor de Next**; el navegador nunca habla con Django. Sin la variable se usa `http://127.0.0.1:8000`.

Para tener contenido que estudiar en local sin pasar por la revisión editorial, en el backend:

```bash
cp db.sqlite3 db.dev.sqlite3
DEBUG=True DATABASE_URL=sqlite:///$PWD/db.dev.sqlite3 python manage.py dev_publish_sample --level 1 --level 2
DEBUG=True DATABASE_URL=sqlite:///$PWD/db.dev.sqlite3 python manage.py runserver 8001
```

y aquí `HANZI_API_URL=http://127.0.0.1:8001 pnpm dev`. Ese comando se niega a correr sobre cualquier base que no termine en `dev.sqlite3`.

## Cómo está conectado

```
Navegador ──▶ /api/auth/{login,register,logout}  (src/app/api/auth)   ──▶ Django /api/v1/auth/…
          ──▶ /api/v1/*                          (src/app/api/v1)     ──▶ Django /api/v1/*
```

- **Credenciales:** las rutas de servidor de Next guardan `access` y `refresh` en cookies httpOnly y reenvían cada petición con `Authorization`. Si el acceso caducó, renuevan una vez y repiten (`src/lib/server/backend.ts`).
- **Datos:** `src/lib/store/db.ts` es una **caché del servidor**, no un servidor simulado. Las pantallas solo usan `lib/store/actions.ts` (peticiones) y `lib/store/selectors.ts` (lecturas de la caché).
- **Respuestas:** se aplican en pantalla al instante (la siguiente tarjeta no espera a la red, Q-03) y van a un buzón en `localStorage` que se envía en orden, con reintentos y espera creciente, también al recargar o al volver la red (R-SES-03, R-SES-04, D-44). Cada respuesta lleva un `client_id`; el servidor la aplica una sola vez.
- **El servidor decide:** la cola, FSRS, la racha, los derechos, la búsqueda y la calificación de escucha y escritura ya no viven en el navegador. El frontend repite solo la regla del refuerzo y de la calificación de escritura para no esperar a la red; si el servidor dice otra cosa, la sesión se recarga desde él (R-SES-07).

## Pantallas

| Ruta | Historias |
|---|---|
| `/` (landing) | HU-E01-01 |
| `/login`, `/signup`, `/recover-access` | HU-E02-01, HU-E02-02 |
| `/today` | HU-E03-01, HU-E06-02, HU-E09-02 |
| `/study` | HU-E03-02/03/04, HU-E04-01/02, HU-E05-01/02/03, HU-E06-01/02/03 |
| `/decks`, `/decks/[deckId]` | HU-E08-01 |
| `/dictionary`, `/dictionary/[wordId]` | HU-E07-01/02/03/04 |
| `/me` | HU-E09-01, HU-E09-02 |
| `/me/settings/*` | HU-E10-01, HU-E10-02, HU-E10-03 |
| `/data-policy`, `/credits` | R-DAT-01, R-CON-15 |

## Pendiente

- **Pruebas de extremo a extremo** (`e2e_*` de `../backend/Docs/historias/`): no existen todavía. Hacen falta Playwright y un backend de prueba.
- **Audio:** sin proveedor de síntesis no hay archivos (`08-contenido.md` §1). En desarrollo, una dirección `tts:` usa la voz del navegador.
- **Trazos:** `hanzi-writer` descarga los datos de cada carácter desde jsDelivr; antes de abrir al público hay que servirlos desde nuestro dominio o nombrar a jsDelivr en la política (R-DAT-11).
- **Registro enlazado desde la landing:** la landing enlaza a `/signup`, y R-CTA-10 lo quería sin enlazar. Falta decidir si se mantiene.
