# 02 · Glosario

**Para qué sirve:** fija un solo nombre por concepto. La columna "Interfaz" es la palabra que ve el usuario en español; la columna "Código" es el identificador en inglés para tablas, clases, rutas y eventos. Si un término no está aquí, no se usa en historias ni en código hasta agregarlo.

**Tope de extensión:** 220 líneas. **Estado:** tercera revisión (22 nov 2026); retira "Ya la sé".

**Convenciones**

- Un concepto, un nombre. La columna "No usar" lista los sinónimos que aparecían en los Workshops, los mockups o el código anterior y que quedan retirados.
- Las reglas se citan por su ID (`R-XXX-nn`) y viven en `03-reglas-de-negocio.md`. Aquí solo hay definiciones.

---

## 1. Personas y acceso

| Interfaz | Código | Definición | No usar |
|---|---|---|---|
| Visitante | — (sin registro en base) | Persona que navega las páginas públicas sin estudiar | — |
| Invitado | `guest` | Persona que estudia en una sesión de prueba sin haberse registrado. Tiene una cuenta anónima sin datos personales (`R-CTA-02`) | usuario anónimo, demo |
| Estudiante | `student` | Persona con cuenta registrada que estudia. Es el único rol de usuario final | usuario (ambiguo), alumno |
| Editor | `staff` con permiso `content` | Quien carga, revisa y publica contenido. Hoy es el fundador | administrador, gestor de contenido |
| Dueño | `staff` con permiso `owner` | Quien ve métricas, atiende soporte, concede accesos y suspende cuentas. Hoy es el fundador | administrador |
| Cuenta | `account` / `user` | Identidad con la que alguien accede y a la que pertenece su progreso | perfil (eso es otra cosa) |
| Acceso | `login` / `auth_session` | Acto de identificarse y periodo durante el cual la cuenta permanece identificada en un dispositivo | sesión, iniciar sesión |
| Cohorte | `cohort` | Grupo de procedencia de una cuenta (por ejemplo, una clase), tomado del enlace de registro. Solo sirve para medir (`R-CTA-10`) | invitación, curso, grupo |
| Perfil | `profile` | Datos y preferencias editables de la cuenta: nombre, idiomas, zona horaria, límites diarios | cuenta |

**Regla de vocabulario:** la palabra **sesión**, sin más, siempre significa sesión de estudio. Para la identificación se dice **acceso** ("Acceder", "Cerrar acceso").

## 2. Idioma

| Interfaz | Código | Definición | No usar |
|---|---|---|---|
| Idioma de la interfaz | `ui_language` | Idioma de botones, menús, mensajes y correos | idioma (a secas) |
| Idioma de estudio | `study_language` | Idioma en el que el estudiante lee significados y traducciones de ejemplos | idioma de contenido |
| Idioma activo | `language.is_study_active`, `language.is_ui_active` | Idioma que el dueño ha habilitado para elegir. Se activa con un interruptor, no con código (`R-IDI-10`) | — |
| Clave de traducción | `translation_key` | Identificador de un texto de interfaz; el texto real está en el catálogo de cada idioma | texto fijo |

## 3. Contenido

| Interfaz | Código | Definición | No usar |
|---|---|---|---|
| Sílabo | `syllabus` | Programa oficial del examen HSK publicado en noviembre de 2025. Es la fuente de la lista de palabras | estándar, lista oficial |
| Nivel | `hsk_level` | Nivel HSK del 1 al 6 al que el sílabo asigna una palabra | banda, grado |
| Palabra | `word` | Entrada del sílabo. Unidad de contenido y de estudio en lectura y escucha | tarjeta, vocablo, término |
| Carácter | `character` | Hanzi individual. Unidad de estudio en escritura | letra, símbolo |
| Dato del sílabo | `syllabus_data` | Lo que el sílabo publica de una palabra: hanzi, pinyin, nivel y número de orden. Se muestra siempre | — |
| Acepción | `sense` | Uno de los significados de una palabra, con su categoría gramatical. Es común a todos los idiomas | significado (eso es su traducción), meaning |
| Ejemplo | `example` | Oración en chino, con pinyin, que ilustra una acepción. Es común a todos los idiomas | frase |
| Base de la palabra | `word_base` | Conjunto de acepciones y ejemplos en chino de una palabra. Tiene su propio estado editorial (`R-CON-04`) | — |
| Significado | `translation` (de una acepción) | Texto en el idioma de estudio que traduce una acepción | glosa, definición |
| Traducción | `translation` (de un ejemplo) | Texto en el idioma de estudio que traduce un ejemplo | — |
| Contenido por idioma | `language_content` | Conjunto de significados y traducciones de una palabra en un idioma. Tiene su propio estado editorial | — |
| Glosa de terceros | `third_party_gloss` | Significado redactado por una fuente externa. Uso interno como ancla de generación; **nunca se muestra** (`R-CON-02`) | — |
| Estado editorial | `editorial_status` | Situación de una base o de un contenido por idioma: `none`, `draft`, `published` | pendiente, aprobado, rechazado |
| Borrador | `draft` | Versión en preparación, invisible para estudiantes | pendiente |
| Publicado | `published` | Versión visible para estudiantes | aprobado |
| En revisión | (etiqueta de interfaz) | Lo que ve el estudiante cuando una palabra no tiene contenido publicado en su idioma de estudio. Agrupa `none` y `draft` | próximamente |
| Versión de contenido | `content_version` | Cada estado guardado de una base o de un contenido por idioma. Solo una está publicada a la vez (`R-CON-05`) | — |
| Validación | `validation` | Comprobación automática sobre un borrador | — |
| Audio | `audio_asset` | Grabación sintetizada de un texto, identificada por el texto, el idioma hablado y la voz | pronunciación (eso es otra función) |
| Voz | `voice` | Voz sintética con la que se genera un audio | — |
| Reporte de error | `content_report` | Aviso de un estudiante sobre un posible error en una palabra | feedback |

## 4. Organización

| Interfaz | Código | Definición | No usar |
|---|---|---|---|
| Mazo | `deck` | Conjunto ordenado de palabras para estudiar | lista, carpeta, colección |
| Mazo del sistema | `deck.kind = system` | Mazo de solo lectura que agrupa palabras de un nivel | mazo HSK, mazo predeterminado |
| Mazo propio | `deck.kind = own` | Mazo creado por un estudiante | mazo personal, mi lista |

Un mazo se mide en **palabras**. No existen "listas" ni "carpetas" que contengan mazos; los mazos del sistema se agrupan por nivel.

## 5. Estudio

| Interfaz | Código | Definición | No usar |
|---|---|---|---|
| Habilidad | `skill` | Lo que se entrena: **lectura** (`recognition`), **escucha** (`listening`) o **escritura** (`writing`) | modo de estudio, tipo de práctica |
| Lectura | `recognition` | Ver el hanzi y recordar pinyin y significado | reconocimiento, flashcards, leer y traducir |
| Escucha | `listening` | Oír la palabra y elegir su significado | listening, habilidad auditiva |
| Escritura | `writing` | Trazar un carácter | — |
| Tarjeta | `card` | Lo que el estudiante responde: una palabra o un carácter presentado en una habilidad. No es una unidad de contenido | palabra (cuando se habla de contenido) |
| Estado de repaso | `review_state` | Memoria que el sistema guarda de un estudiante sobre un ítem en una habilidad: estabilidad, dificultad y próxima fecha | estado FSRS, progreso |
| Nueva | `new` | Tarjeta sin estado de repaso en esa habilidad | — |
| Pendiente | `due` | Tarjeta cuyo próximo repaso cae hoy o antes (`R-REP-04`) | vencida, atrasada, para revisar |
| Calificación | `grade` | Resultado de una respuesta: **Recordé** (`pass`) o **No recordé** (`fail`). No hay más | fácil, difícil, otra vez, bien, easy, hard |
| Recordé / No recordé | `pass` / `fail` | Las dos calificaciones posibles de una tarjeta ya vista | Lo sabía / No lo sabía, Fácil / Difícil |
| Respuesta | `answer` | Registro de una calificación, con su identificador único de cliente (`R-SES-03`) | repaso, review log |
| Sesión | `study_session` | Recorrido de una cola de tarjetas de una sola habilidad | — |
| Sesión programada | `kind = scheduled` | Sesión cuyas respuestas actualizan el calendario de repasos | Estudiar pendientes |
| Repaso libre | `kind = free` | Sesión sobre todo un mazo que no cambia ningún estado de repaso | Repasar todo, solo ver |
| Todos los pendientes | `scope = all_due` | Sesión programada que reúne lo pendiente de todos los mazos | — |
| Cola | `queue` | Lista ordenada de tarjetas de una sesión, fijada al empezar | — |
| Reanudar | `resume` | Continuar una sesión en la tarjeta exacta donde quedó | continuar |
| Descartar | `discard` | Cerrar una sesión sin terminarla; lo ya respondido se conserva | empezar de nuevo |
| Deshacer | `undo` | Anular la última respuesta de la sesión en curso | — |
| Refuerzo | `reinforcement` | Reaparición, en la misma sesión, de una tarjeta que se falló. No cambia el calendario (`R-REP-05`) | reaprendizaje |
| Límite diario de nuevas | `daily_new_limit` | Máximo de tarjetas nuevas por día y por habilidad | — |
| Aprendida / Aprendido | `learned` | Palabra (en lectura) o carácter (en escritura) con estabilidad de 21 días o más | dominada |

## 6. Escritura

| Interfaz | Código | Definición | No usar |
|---|---|---|---|
| Con guía | `mode = guided` | Práctica con el contorno del carácter visible. No cambia el calendario | modo fácil, easy |
| De memoria | `mode = recall` | Escritura sin contorno. Es la única que cambia el calendario (`R-ESC-02`) | modo difícil, hard, quiz |
| Trazo errado | `stroke_miss` | Intento de trazo que el reconocedor rechaza | error |
| Pista | `hint` | Mostrar el trazo siguiente, pedida por el estudiante o automática | ayuda |

## 7. Progreso y hábito

| Interfaz | Código | Definición | No usar |
|---|---|---|---|
| Día | `local_day` | Día del estudiante según su zona horaria, que empieza a las 4:00 a. m. (`R-PRO-01`) | fecha |
| Estado del día | `day_status` | Clasificación de un día ya cerrado: activo, exento o fallado (`R-PRO-03`, `R-PRO-09`) | — |
| Día activo | `active` | Día en que el estudiante dio al menos una respuesta que cambió su calendario | día de estudio |
| Día exento | `exempt` | Día sin actividad en el que no había nada pendiente. No rompe la racha ni la aumenta | día libre, día de descanso |
| Día fallado | `missed` | Día sin actividad en el que sí había algo pendiente. Rompe la racha | — |
| Racha | `streak` | Número de días activos desde el último día fallado (`R-PRO-04`) | — |
| Meta de examen | `exam_goal` | Nivel y fecha de examen que el estudiante declara, con el ritmo diario sugerido | misión, objetivo |
| Recordatorio | `reminder` | Correo opcional que avisa cuando el día aún no está activo | notificación |

## 8. Planes, derechos y cuotas

| Interfaz | Código | Definición | No usar |
|---|---|---|---|
| Plan | `plan` | Paquete con nombre comercial (Free, Pro) que agrupa derechos | suscripción (es una forma de pago, no un plan) |
| Derecho de acceso | `entitlement` | Permiso para usar una capacidad: estudiar un nivel, crear mazos, evaluar pronunciación | permiso, feature |
| Capacidad | `capability` | Cosa concreta que se puede permitir, limitar o medir. Ejemplo: `study.level.3` | función |
| Límite | `limit` | Tope de cuántos objetos puede tener un estudiante a la vez. Ejemplo: 10 mazos propios | cuota |
| Cuota de uso | `usage_quota` | Tope de cuántas veces se puede usar, por periodo, una capacidad con costo variable | límite |
| Consumo | `usage_record` | Anotación de un uso descontado de una cuota | — |
| Concesión | `grant` | Hecho por el cual una cuenta recibe derechos: plan por defecto, compra, promoción u otorgamiento manual, con fecha de inicio y de fin | licencia |
| Compra | `purchase` | Pago que origina una concesión | pedido |
| Bloqueado | `locked` | Estado en que se muestra algo que existe pero que el plan no incluye | oculto |

## 9. Datos personales y voz

| Interfaz | Código | Definición | No usar |
|---|---|---|---|
| Política de datos | `data_policy` | Documento versionado de tratamiento de datos personales | términos |
| Consentimiento | `consent` | Autorización del titular para una finalidad concreta, con versión y fecha. Hay uno por finalidad | aceptación |
| Finalidad | `consent.purpose` | Para qué se autoriza: `general`, `reminder_email`, `voice_recording` | — |
| Grabación de voz | `voice_recording` | Audio de la voz del estudiante. Dato sensible; solo existirá con la función de pronunciación (`R-DAT-08`) | audio (eso es el sintético) |
| Plazo de conservación | `retention_period` | Tiempo tras el cual un dato se borra automáticamente | — |
| Exportación | `data_export` | Archivo con todos los datos de la cuenta, generado a petición del titular | descarga |

## 10. Operación

| Interfaz | Código | Definición | No usar |
|---|---|---|---|
| Evento de analítica | `analytics_event` | Hecho de uso registrado para medir el producto, sin datos personales | log, tracking |
| Interruptor | `feature_flag` | Ajuste que activa o desactiva una función o un idioma sin desplegar código | toggle, config |
| Registro de auditoría | `audit_log` | Anotación de una acción del editor o del dueño | historial |

## 11. Términos retirados

Vienen de los Workshops, los mockups o el README y **no** forman parte del producto ni de esta documentación: *misión*, *lista* y *carpeta* (como contenedores de mazos), *profesor*, *curso*, *inscripción*, *modo solo ver*, *repasar errores* como modo aparte, *insignia*, *mock exam* propio, *Max* (plan), *Ya la sé* y su marca `declared_known` (retirados por D-42).
