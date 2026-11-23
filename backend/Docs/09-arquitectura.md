# 09 · Arquitectura

**Para qué sirve:** una vista general de las piezas y de los cuatro flujos donde un error de diseño sale caro. No describe pantallas ni sustituye al esquema de base de datos, que es código. Si un flujo cambia aquí, cambia antes en `03-reglas-de-negocio.md`.

**Tope de extensión:** 200 líneas. **Estado:** segunda versión (22 nov 2026): nombres reales de los módulos y contrato en `10-api.md`. Decisiones de base: `D-23`, `D-24`, `D-32`, `D-34`, `D-37`.

---

## 1. Esquema general

```
Navegador (móvil primero)
  │  HTTPS
  ▼
Interfaz — Next.js en Vercel
  · Páginas y componentes; textos solo por clave de traducción
  · Rutas de servidor: guardan la credencial en cookie httpOnly y reenvían a la API
  · Buzón de salida local (localStorage, D-44) con las respuestas aún no confirmadas
  │  HTTPS, JSON
  ▼
API — Django (monolito modular) en Railway
  · Vistas → servicios → modelos. La lógica vive en los servicios
  · Tareas programadas: cierre del día, recordatorios, borrados por plazo, copias
  │                         │                         │
  ▼                         ▼                         ▼
PostgreSQL (Railway)   Cloudflare R2             Servicios externos
  única fuente           · audio (público)         · correo transaccional
  de verdad              · voz (privado, V4)       · acceso con Google
                                                   · síntesis de voz (al generar contenido)
                                                   · evaluación de pronunciación (V4)
```

La generación de contenido con IA **no** forma parte de la aplicación en ejecución: son comandos que el editor lanza y que dejan borradores en la base (`D-13`).

## 2. Módulos del servidor

Un módulo solo depende de los que están por encima de él en la tabla. Nadie lee las tablas de otro módulo directamente; se usa su servicio. `analytics` (emitir eventos) y `ops` (parámetros y auditoría) son infraestructura: cualquier módulo los usa, y ellos solo leen de `accounts` y `entitlements` lo necesario para los campos comunes.

| Módulo | Qué posee | Reglas |
|---|---|---|
| `accounts` (app `users`, nombre heredado) | Cuentas, acceso, perfil, cohorte, intentos fallidos | R-CTA |
| `languages` | Idiomas, interruptores, catálogos de interfaz | R-IDI |
| `content` | Palabras, caracteres, base, contenido por idioma, versiones, audio, reportes | R-CON |
| `entitlements` | Capacidades, planes, concesiones, límites, cuotas y consumos | R-DER |
| `decks` | Mazos del sistema y propios | R-MAZ |
| `scheduling` | Estados de repaso e historial; adaptador de FSRS | R-REP, R-ESC-03 |
| `study` | Sesiones, colas, respuestas, reanudación | R-SES, R-ESC |
| `progress` | Estado del día, racha, avance, meta de examen | R-PRO |
| `privacy` | Política, consentimientos, exportación, eliminación, grabaciones de voz | R-DAT |
| `analytics` | Eventos y consultas del tablero | R-DAT-07, R-IDI-13 |
| `ops` | Auditoría, interruptores, parámetros ajustables | R-DAT-10 |

Cada módulo expone sus rutas en `<módulo>/urls.py`, montadas bajo `/api/v1/` (`10-api.md`). Las apps heredadas `vocab` y `UserProgress` quedan sin rutas y solo se conservan por sus datos.

Tres decisiones de forma que evitan deuda:

- **`scheduling` no sabe de sesiones ni de mazos.** Recibe "esta cuenta respondió esto sobre este ítem en esta habilidad" y devuelve el estado nuevo. FSRS está detrás de una interfaz (`R-REP-02`).
- **El estado de repaso es genérico:** una fila por cuenta, habilidad y unidad, donde la unidad es una palabra o un carácter. Una cuarta habilidad no pide una tabla nueva.
- **`progress` escucha, no pregunta.** Recibe el aviso "se registró una respuesta" (señal `answer_recorded` de `study`) y actualiza lo suyo, de modo que `study` no depende de `progress`.
- **Borrar una cuenta es un registro.** Cada módulo registra en `privacy` qué guarda de una cuenta y cómo borrarlo; `privacy` no conoce las tablas de nadie.

## 3. Flujo 1 — Guardado idempotente

Objetivo: ninguna respuesta se pierde ni se aplica dos veces (`R-SES-03`, `R-SES-04`, `R-SES-07`, `R-SES-11`).

```
Dispositivo                                   Servidor (una sola transacción)
───────────                                   ──────────────────────────────
1. El estudiante responde
2. Genera un identificador único
3. Escribe la respuesta en el buzón local
4. Muestra ya la siguiente tarjeta
5. Envía la respuesta ───────────────────────▶ a. Bloquea la sesión
                                               b. ¿Identificador ya visto para esta cuenta?
                                                    sí → devuelve el resultado guardado
                                               c. ¿Es una tarjeta sin responder de esta sesión?
                                                    no → rechaza y devuelve la posición actual
                                               d. Escritura: calcula la calificación (R-ESC-03)
                                               e. Si cambia el calendario: llama a scheduling
                                               f. Guarda respuesta, historial, estado y posición
                                               g. Anota el evento de analítica en la misma transacción
6. Recibe confirmación ◀────────────────────── h. Confirma y devuelve posición y resultado
7. Borra la respuesta del buzón local
```

- Si el paso 5 falla, la respuesta sigue en el buzón y se reintenta con espera creciente, también al reabrir la página.
- El identificador es único por cuenta, con restricción en la base: la garantía no depende del código.
- El paso 4 no espera a la red. Lo que el estudiante ve como "respondida" y lo que el servidor ha confirmado pueden diferir unos instantes; un indicador discreto muestra si hay respuestas por confirmar.
- El mismo mecanismo (identificador único y transacción) se usa para los consumos de cuota (`R-DER-09`).

## 4. Flujo 2 — Reanudación exacta

Objetivo: volver a la tarjeta o al carácter exacto, en cualquier dispositivo (`R-SES-05`, `R-SES-06`, `R-ESC-07`).

1. Al iniciar una sesión, el servidor calcula la cola y la **guarda** con su orden. No se vuelve a calcular.
2. Al abrir la aplicación, el dispositivo vacía primero su buzón local y después pide las sesiones en curso.
3. Para reanudar, el servidor devuelve la cola con el estado de cada tarjeta: respondida, sin responder o "ya repasada" (su estado cambió hoy por otra vía).
4. El dispositivo se sitúa en la primera sin responder. En escritura, un carácter a medias empieza limpio.
5. Si dos dispositivos tienen la misma sesión abierta, el paso (c) del flujo 1 resuelve el conflicto: gana la primera respuesta que llega y el otro dispositivo se reubica.

La sesión guarda lo necesario para reconstruir la pantalla sin estado del dispositivo: habilidad, alcance, tipo, cola y, en escritura, el modo.

## 5. Flujo 3 — Contenido y audio

Objetivo: que nada llegue a un estudiante sin revisión, y que corregir no rompa nada (`R-CON-04` a `R-CON-07`, `R-CON-11`, `R-CON-13`).

```
Sílabo oficial ──▶ comando de carga ──▶ palabras con datos del sílabo (estado: sin contenido)
                                              │
Glosas de terceros (campo interno) ──▶ comando de generación ──▶ BORRADOR de base y de contenido por idioma
                                              │                         │
                                              ▼                         ▼
                                     validaciones automáticas   síntesis de voz ──▶ R2 (audio)
                                              │
                              Panel de Django: revisar, editar (revalida), publicar
                                              │
                         Publicar = cambiar la versión publicada en una transacción
                                              │
                                              ▼
                              Lo que ve el estudiante (solo versiones publicadas)
```

- **Las lecturas de estudiantes solo consultan versiones publicadas.** Un borrador no puede filtrarse por un descuido en una consulta, porque vive en otra versión.
- **El progreso apunta al identificador estable de la palabra**, no a una versión. Corregir un significado no toca ningún estado de repaso.
- **Audio:** la ruta del archivo se deriva del idioma hablado, la voz y una huella del texto. El mismo texto con la misma voz nunca se genera dos veces, y cambiar de voz no pisa lo anterior (`R-IDI-08`). El audio de contenido no es dato personal y se sirve desde una dirección pública con caché.
- **Voz del estudiante (V4):** otro contenedor, privado, sin dirección pública, con acceso por enlaces temporales y una regla de caducidad igual a `voice_retention_days`. Nunca comparte contenedor con el audio de contenido (`R-DAT-08`).

## 6. Flujo 4 — Derechos de acceso y cuotas

Objetivo: una sola respuesta a "¿puede esta cuenta hacer esto?", válida para cualquier forma de cobro (`R-DER-01` a `R-DER-13`).

```
Plan (dato versionado) ──┐
                         ├──▶ Concesiones de la cuenta ──▶ Derechos vigentes ──▶ puede(cuenta, capacidad, recurso)
Compra / manual / promo ─┘     (origen, alcance, inicio, fin)   (unión; rige el mayor)          │
                                                                                 ┌─────────────┼──────────────┐
                                                                                 ▼             ▼              ▼
                                                                              acceso         límite          cuota
                                                                             (sí / no)   (cuenta objetos)  (consumos)
```

- **Un único punto de decisión.** La construcción de colas, la creación de mazos y la evaluación de pronunciación llaman a la misma función. La interfaz la consulta para mostrar candados, pero no decide.
- **El plan no está escrito en el código.** Free y Pro son filas; "HSK 1 y 2" es la lista de capacidades `study.level.1` y `study.level.2`. Vender un nivel suelto es conceder una capacidad; vender un pase es conceder el plan con fecha de fin.
- **Uso de una cuota** (pronunciación, V4): reservar el consumo → llamar al servicio externo → confirmar, o revertir si falla. Reserva y confirmación comparten identificador, así que un reintento no cobra dos veces.
- **Freno de costos:** antes de reservar se comprueban el interruptor global y el tope de gasto mensual (`R-DER-10`).
- **Caché:** los derechos vigentes de una cuenta se pueden guardar en caché, y se invalidan al crear, cambiar o vencer una concesión (`R-DER-13`).

## 7. Otros puntos transversales

| Tema | Cómo se resuelve |
|---|---|
| Cierre del día | Una tarea clasifica cada día cerrado como activo, exento o fallado y lo guarda (`R-PRO-09`). Si la tarea no ha corrido, se calcula al primer acceso del estudiante |
| Idiomas | La interfaz lee catálogos por clave; el servidor devuelve claves de error, no textos. El contenido se filtra por idioma de estudio en el servicio de `content` |
| Analítica | Tabla propia en PostgreSQL, escrita en la misma transacción que el hecho que mide. Sin servicios de terceros en V1 |
| Eliminación de cuenta | Un servicio de `privacy` recorre todos los módulos; cada módulo declara qué guarda de una cuenta y cómo borrarlo |
| Credenciales | Next guarda `access` y `refresh` en cookies httpOnly y reenvía `/api/v1/*` a Django con `Authorization` (`10-api.md`, sección 2) |
| Base de datos | `DATABASE_URL` elige PostgreSQL; sin ella, SQLite local para desarrollo |
| FSRS | Librería `fsrs` 6.3.3 fijada, con pasos de aprendizaje vacíos (intervalos en días) y sin aleatoriedad, para que las pruebas de referencia sean reproducibles (`Q-22`) |
| Parámetros | Los valores de la sección 11 de las reglas viven en una tabla de `ops`, con auditoría |
| Zona horaria | La base guarda instantes en UTC; el día local se calcula con la zona de la cuenta y la hora de corte |

## 8. Lo que esta arquitectura no resuelve todavía

- **Un solo servidor y una sola base.** Suficiente para V1 y V2; no hay redundancia. El objetivo de disponibilidad de `06-calidad.md` está fijado en consecuencia.
- **La frontera entre Vercel y Railway** añade un salto de red a cada petición. Si la latencia del guardado no cumple `Q-01`, la primera medida es que el dispositivo hable directo con la API para las respuestas.
- **Búsqueda.** Con unas 5.400 palabras basta la búsqueda de texto de PostgreSQL. No se añade un motor aparte.
