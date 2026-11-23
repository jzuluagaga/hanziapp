# 01 · Visión y alcance

**Para qué sirve:** dice para quién es HanziApp, qué problema resuelve, qué entra en cada versión y qué no entra nunca. Si una historia nueva no encaja aquí, primero se discute este archivo.

**Tope de extensión:** 120 líneas. **Estado:** primera versión (22 nov 2026). Se apoya en `EVALUACION-PRODUCTO.md` (15 nov 2026), que no se mantiene.

---

## 1. En una frase

HanziApp ayuda a hispanohablantes que preparan el HSK 1 a 3 a **llegar tranquilos al examen**: cada día les dice qué repasar, en lectura, escucha y escritura, con contenido en español revisado por una persona, y nunca les hace perder lo que ya estudiaron.

## 2. Para quién

| Segmento | Qué necesita | Prioridad |
|---|---|---|
| **A. Alumno de Instituto Confucio o de curso universitario en Latinoamérica, HSK 1 a 3, con fecha de examen** | Repasar el vocabulario de clase y llegar al examen sin quedarse atrás | **Primero.** Hay canal (el profesor), usuarios previos y ventaja de idioma |
| B. Hispanohablante que prepara HSK 3 o 4 para una beca | Aprobar con puntaje mínimo en una fecha fija | Después de V1, cuando haya contenido revisado de HSK 3 |
| C. Autodidacta por gusto | Hábito y sensación de avance | No se diseña para él; si llega, bien |

Cuando A y el fundador (HSK 3) quieran cosas distintas, manda A (`D-02`).

**El competidor real no es otra app: es no hacer nada.** El alumno de instituto que hoy repasa con el cuaderno es el que puede cambiar.

## 3. Qué problema resuelve y qué no

| Resuelve | No resuelve (y no lo intenta) |
|---|---|
| Saber qué repasar hoy, con repetición espaciada (FSRS) | Enseñar gramática o lectura en contexto |
| Oír cada palabra y reconocerla al oído, que es media prueba de HSK 1 y 2 | Simulacros de examen: existe el oficial (`D-03`) |
| Significados y ejemplos en español natural, revisados | Traducir a muchos idiomas a la vez (`D-06`) |
| No perder el progreso de una sesión, la causa de abandono del MVP anterior | Funcionar sin conexión (`D-03`) |
| Escribir caracteres de memoria con calificación objetiva | Evaluar la pronunciación antes de V4 (`D-04`) |

## 4. Principios de producto

1. **Medir antes de construir.** V2 no se detalla hasta medir V1 con una clase real durante cuatro semanas (`D-05`).
2. **Nada se pierde.** Cada respuesta se guarda una sola vez y se reanuda donde quedó (`D-23`, `D-24`).
3. **Dos botones.** "Recordé" y "No recordé"; sin "Ya la sé" ni "Fácil" (`D-15`, `D-42`).
4. **Contenido revisado o nada.** Lo que no pasó revisión humana se ve como "en revisión" (`D-09`, `D-12`).
5. **El diccionario es gratis; se paga el estudio** (`D-10`).
6. **Un solo punto decide los derechos**, aunque hoy nadie pague (`D-34`).
7. **Preparado para un segundo idioma** sin tocar código ni esquema (`D-06`, `R-IDI-10`).

## 5. Alcance por versión

| Versión | Objetivo | Qué entra | Compuerta de salida |
|---|---|---|---|
| **V1a** | Poner el producto en manos de una clase y empezar a medir | Contenido HSK 1 y 2 publicado; cuenta; lectura y escucha con FSRS; guardado y reanudación; racha; tablero de retención | Usable por una clase real |
| **V1b** | Completar la experiencia mientras V1a está en uso | Escritura; diccionario con búsqueda y reportes; progreso; perfil; eliminación de cuenta | — |
| **V2** | Que cualquiera llegue, pruebe y se quede sin ayuda | Páginas públicas por nivel, invitado, Google, mazos propios, meta de examen, deshacer, repaso libre | Retención de la semana 4 de 35 % o más (`M-02`) |
| **V3** | Primer ingreso | Cobro (pase Pro por tiempo, `D-35`), HSK 3 en adelante con revisor, recordatorios | — |
| **V4** | Pronunciación | Evaluación de voz con servicio externo, solo Pro, con cuota (`D-37`) | — |

El detalle de cada historia está en `05-mapa-de-historias.md` y, para V1, en `historias/`.

## 6. Fuera del producto

Cursos y rol de profesor, simulacros propios, diccionario más allá del sílabo HSK 1–6, aplicación nativa, modo sin conexión, plan Max, insignias (`D-03`, `D-33`).

## 7. Cómo sabremos si funciona

| Pregunta | Métrica | Umbral |
|---|---|---|
| ¿Vuelven? | `M-02`, retención en la semana 4 | 35 % seguir; 15–35 % cambiar una cosa; menos de 15 % en dos clases, parar |
| ¿Aprenden? | `M-04`, retención real por intervalo | Cerca de `fsrs_target_retention` (0,90) |
| ¿Se pierde algo? | `M-09`, entregas demoradas, y `Q-02` | Cero respuestas perdidas |

## 8. Riesgos principales

| Riesgo | Mitigación |
|---|---|
| Nadie vuelve después de la primera semana | La compuerta de V1 lo detecta en cuatro semanas, antes de construir V2 |
| Errores de contenido que vea un profesor | Revisión humana obligatoria y reportes desde la ficha (`R-CON-07`, `R-CON-14`) |
| Contenido por encima de HSK 2 sin revisor competente | No se publica sin revisor del nivel (`D-08`) |
| Una sola persona desarrolla y opera | Alcance recortado, documentación verificable y pruebas por criterio (`Q-25`) |
| Condiciones de uso del audio y de la IA sin verificar | No se cobra por el contenido hasta verificarlas (`08-contenido.md`, sección 1) |
