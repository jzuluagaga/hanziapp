# 00 · Índice

**Para qué sirve:** es la puerta de entrada a la documentación de HanziApp. Dice qué archivo responde cada pregunta, cómo se nombran las cosas y cuándo una historia está lista para construirse o terminada.

**Tope de extensión:** 150 líneas. **Estado:** segunda versión (22 nov 2026).

---

## 1. Documentos

| Archivo | Responde a | Estado |
|---|---|---|
| `00-indice.md` | ¿Dónde está cada cosa y con qué convenciones? | Primera versión |
| `01-vision-y-alcance.md` | ¿Para quién es, qué entra y qué no? | Primera versión |
| `02-glosario.md` | ¿Cómo se llama cada concepto en la interfaz y en el código? | Revisado |
| `03-reglas-de-negocio.md` | ¿Qué debe cumplirse siempre? | Revisado; propuestas y supuestos en su sección 12 |
| `04-decisiones.md` | ¿Qué se decidió, por qué y qué se descartó? | Primera versión |
| `05-mapa-de-historias.md` | ¿Qué historias hay, en qué versión y en qué orden? | Revisado |
| `06-calidad.md` | ¿Qué umbrales medibles debe cumplir el producto? | Primera versión |
| `07-eventos-y-metricas.md` | ¿Qué se mide y cómo se calcula? | Primera versión |
| `08-contenido.md` | ¿Cómo se produce, revisa y publica el contenido? | Primera versión |
| `09-arquitectura.md` | ¿Qué piezas hay y cómo son los cuatro flujos delicados? | Primera versión |
| `10-api.md` | ¿Qué rutas expone el servidor y qué devuelven? | Primera versión |
| `historias/E<nn>-<nombre>.md` | ¿Qué debe hacer exactamente cada historia de V1? | Primera versión (35 historias, 160 criterios) |
| `tools/verificar_docs.py` | ¿La documentación es coherente consigo misma? | Funciona |

Antecedentes que no se mantienen: `REVISION-ELICITACION.md` y `EVALUACION-PRODUCTO.md`.
## 2. Los Workshops son históricos

Las entregas del curso de Ingeniería de Software II (`hanziapp/Workshop-1/`, `hanziapp/Workshop-2/`, los diagramas de clases, el modelo relacional, los BPMN, la arquitectura y los mockups) **quedan como documentos históricos**. Esta carpeta `docs/` los reemplaza como base para programar el producto.

- Sus identificadores (RF, RNF, RN y HU numeradas del curso) **no** tienen equivalencia aquí y no deben citarse.
- Donde un Workshop y `docs/` se contradigan, vale `docs/`.
- Diferencias de fondo: no hay cursos ni rol de profesor; dos calificaciones en vez de cuatro; escritura con FSRS; reanudación exacta sin recálculo; verificación de correo no bloqueante; mazos sin listas; contenido solo en español; sin Supabase. Todas están en `04-decisiones.md`.

## 3. Identificadores

| Prefijo | Qué identifica | Dónde se define | Ejemplo |
|---|---|---|---|
| `R-<área>-<nn>` | Regla de negocio | `03-reglas-de-negocio.md` | `R-SES-06` |
| `D-<nn>` | Decisión | `04-decisiones.md` | `D-16` |
| `HU-E<nn>-<nn>` | Historia | `05-mapa-de-historias.md` | `HU-E03-02` |
| `Q-<nn>` | Requisito de calidad | `06-calidad.md` | `Q-02` |
| `M-<nn>` | Métrica | `07-eventos-y-metricas.md` | `M-02` |
| `nombre_en_ingles` | Evento de analítica | `07-eventos-y-metricas.md` | `answer_recorded` |
| `test_…`, `e2e_…`, `load_…` | Prueba automática | La historia o el requisito que la exige | `test_e03_02_reveal_in_two_steps` |

Reglas de uso:

1. Un identificador **nunca** se reutiliza ni se renumera. Lo que se elimina queda marcado como retirado.
2. Cada cosa se escribe en un solo archivo y los demás la citan. Una historia no repite el texto de una regla.
3. Antes de usar un término nuevo, se agrega al glosario; antes de citar una regla o un evento nuevo, se agrega a su archivo.

## 4. Formato de una historia

```
### HU-E03-02 · Título
**Como** … **quiero** … **para** …
**Corte:** V1a · **Tipo:** U · **Reglas:** R-… · **Necesita:** HU-…

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado … cuando … entonces … | `test_e03_02_…` |

- **Derechos:** qué capacidad consulta y qué ve quien no la tiene
- **Idioma:** qué claves añade y si depende del idioma de estudio
- **Guardado:** qué pasa si se cae la red o se cierra la pestaña
- **Analítica:** `evento`, `evento`
- **Datos personales:** qué guarda de la persona; exportación y borrado
- **Fuera de alcance:** lo que podría esperarse y no entra
```

- Las historias son por resultado del usuario; una historia puede tener muchos criterios.
- Cada criterio tiene **una** prueba con nombre único. El prefijo `test_` es una prueba del servidor; `e2e_`, una de extremo a extremo en el navegador; `load_`, una de carga.
- Las cinco declaraciones son obligatorias. Si una no aplica, se escribe "no aplica".
- Los criterios cubren los casos de excepción; no hay historias sin al menos un caso de error.

## 5. Cuándo una historia está lista para construirse

1. Su versión está abierta: V1, o una posterior cuya compuerta ya se pasó (`05-mapa-de-historias.md`, sección 1).
2. Las historias de su campo "Necesita" están terminadas.
3. Ninguna de sus reglas está marcada como propuesta o supuesto abierto que la bloquee (`03-reglas-de-negocio.md`, sección 12).
4. Tiene criterios con prueba y las cinco declaraciones.
5. El verificador no da errores.

## 6. Cuándo una historia está terminada

1. Todas las pruebas de sus criterios existen con ese nombre y pasan (`Q-25`).
2. No baja la cobertura exigida ni rompe ningún requisito de `06-calidad.md` que ya se cumplía.
3. Sus textos están en los catálogos de todos los idiomas cargados (`R-IDI-04`).
4. Emite los eventos que declara, con el esquema del catálogo (`Q-14`).
5. Lo que guarda de la persona se exporta y se borra con la cuenta (`Q-15`, desde V1b).
6. Está desplegada y la has usado tú en un teléfono real.

## 7. Topes de extensión

Cada archivo declara su tope en la cabecera y el verificador lo comprueba. Si un archivo no cabe, se divide o se recorta; no se sube el tope sin anotarlo en el registro de cambios.

| Archivo | Tope |
|---|---|
| `00-indice.md` | 150 |
| `01-vision-y-alcance.md` | 120 |
| `02-glosario.md` | 220 |
| `03-reglas-de-negocio.md` | 350 |
| `04-decisiones.md` | 200 |
| `05-mapa-de-historias.md` | 260 |
| `06-calidad.md` | 140 |
| `07-eventos-y-metricas.md` | 180 |
| `08-contenido.md` | 170 |
| `09-arquitectura.md` | 200 |
| `10-api.md` | 260 |
| Cada archivo de `historias/` | 160 |

## 8. Verificador

```
python3 docs/tools/verificar_docs.py            # coherencia de la documentación
python3 docs/tools/verificar_docs.py --tests .  # además, que cada prueba citada exista en el código
```

Comprueba, y falla si no se cumple:

| Comprobación | Requisito |
|---|---|
| Toda regla, decisión, requisito, métrica e historia citada existe | `Q-30` |
| Ningún archivo supera su tope | `Q-30` |
| Toda historia de V1 del mapa está detallada, en el archivo de su épica y con el mismo corte | `Q-30` |
| Cada criterio tiene prueba, y ningún nombre de prueba se repite | `Q-25` |
| Cada historia tiene las cinco declaraciones | `Q-30` |
| Todo evento que una historia declara está en el catálogo | `Q-14` |
| Con `--tests`: cada prueba citada existe en el código | `Q-25` |

Avisa, sin fallar, de las reglas que ninguna historia cita y de los archivos sin tope declarado. Debe ejecutarse en la integración continua (`Q-27`).

## 9. Registro de cambios

| Fecha | Cambio |
|---|---|
| 15 nov 2026 | Primera versión de todos los documentos y del verificador; segunda revisión de `02`, `03` y `05` con las decisiones del fundador. Propuestas `D-38` a `D-41`. |
| 22 nov 2026 | Cerradas las decisiones que bloqueaban V1a. Sin "Ya la sé" (`D-42`) y mazos del sistema con tamaño creciente por nivel (`D-43`). Escritos `01`, `10` y las 35 historias de V1 en `historias/`. El frontend ya no guarda copias: la única fuente es `backend/Docs/`. |
| 22 nov 2026 | Decisiones D-45 (Google en V1b), D-46 (registro enlazado), D-47 (modo de escritura elegido) y D-48 (escritura solo de la lista oficial 书写字, 700 caracteres, 50 y 50 en HSK 1 y 2, `R-ESC-10`); D-41 y D-44 firmes. |
| 22 nov 2026 | Mazos por tema (`D-49`): 11 temas y 46 subtemas; las 5.400 palabras clasificadas con la API (unos 1 USD), HSK 1 y 2 aprobados por el fundador y armados en 14 y 11 mazos. Reglas en `08-contenido.md` §7. |

## 10. Pendiente

- Confirmar R-ESC-09 antes de V1b (`03-reglas-de-negocio.md`, sección 12).
- Revisar y aprobar los temas de HSK 3 a 6 antes de publicarlos (unas 1.800 dudosas, casi todas en HSK 5 y 6).
- Cerrar la síntesis de voz con Google (en gestión) y verificar sus condiciones: sin audio no se puede publicar (`08-contenido.md`, sección 1).
- Validación legal de lo marcado **LEGAL** en `03-reglas-de-negocio.md`.
