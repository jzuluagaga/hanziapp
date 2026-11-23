# 04 · Decisiones

**Para qué sirve:** deja constancia de qué se decidió, por qué y qué se descartó, para no volver a discutirlo ni contradecirlo sin darse cuenta. Una decisión no se edita: si cambia, se añade otra que la sustituye y la anterior se marca como sustituida.

**Tope de extensión:** 200 líneas. **Estado:** segunda versión (22 nov 2026): cerradas las decisiones que bloqueaban V1a.

**Convenciones**

- ID: `D-nn`. No se reutiliza.
- Estado: **Firme** (decidida por el fundador), **Propuesta** (recomendación pendiente de su confirmación), **Abierta** (sin decidir), **Sustituida**.
- "Reglas" indica dónde quedó escrita en `03-reglas-de-negocio.md`.

---

## 1. Producto y alcance

| ID | Decisión | Por qué | Descartado | Estado | Reglas |
|---|---|---|---|---|---|
| D-01 | HanziApp es a la vez la herramienta de estudio del fundador y un negocio. Lo desarrolla una sola persona | El equipo del curso no continúa | Limitar el alcance por tamaño de equipo | Firme | — |
| D-02 | Cuando las necesidades del fundador (HSK 3) y las del alumno de instituto (HSK 1–2) choquen, manda el alumno de instituto. El fundador es el primer usuario de cada nivel nuevo | Es el único segmento con canal, usuarios previos y ventaja de idioma (`EVALUACION-PRODUCTO.md`, sección 5.1) | Optimizar para el autodidacta de redes | Firme | — |
| D-03 | Quedan fuera del producto: cursos y rol de profesor, simulacros de examen propios, diccionario más allá de HSK 1–6, aplicación nativa y modo sin conexión | Son otro producto, o ya existe una alternativa oficial o gratuita mejor | — | Firme | — |
| D-04 | La pronunciación va en V4 mediante un servicio externo y solo en Pro | Costo variable y tecnología que no conviene construir | Evaluación de pronunciación propia | Firme | R-DER-05, R-DER-10 |
| D-05 | V1 se entrega en dos cortes (V1a y V1b), y V2 no se detalla ni se construye hasta medir la retención de V1 con una clase real | Nadie ha medido todavía si los usuarios vuelven | Construir todo antes de medir | Firme | `05-mapa`, sección 1 |

## 2. Idioma y contenido

| ID | Decisión | Por qué | Descartado | Estado | Reglas |
|---|---|---|---|---|---|
| D-06 | **El contenido se lanza solo en español.** La interfaz y el modelo se construyen para que añadir inglés sea cargar contenido, publicarlo y encender un interruptor, sin migraciones, sin cambios de código y sin despliegue. **Sustituye a la decisión anterior de un MVP bilingüe** | El inglés duplica la revisión humana, que es el costo dominante, y entra en el segmento con más competidores | MVP bilingüe (decisión del curso, sustituida) | Firme | R-IDI-01 a R-IDI-13 |
| D-07 | El catálogo de interfaz en inglés se mantiene completo desde el primer día aunque esté inactivo, y un idioma ficticio se usa en las pruebas | Es la única forma de comprobar que la promesa de D-06 se cumple | Traducir la interfaz "cuando haga falta" | Firme | R-IDI-04, R-IDI-10 |
| D-08 | Se lanza con HSK 1 y 2 revisados por el fundador. De HSK 3 en adelante solo se publica con un revisor que domine el nivel | El fundador tiene HSK 2 y no puede responder por contenido superior | Publicar los seis niveles con revisión por muestreo | Firme | R-CON-07 |
| D-09 | El diccionario contiene exactamente las palabras del sílabo HSK 1–6. De una palabra sin contenido revisado solo se muestran sus datos del sílabo con el aviso "en revisión". Nunca se muestran glosas redactadas por terceros | La lista del sílabo es dato público; las glosas de terceros no son nuestras | Diccionario general de 120.000 entradas; mostrar la glosa en inglés mientras tanto | Firme | R-CON-01, R-CON-02, R-CON-08 |
| D-10 | **El diccionario es gratuito en todos los niveles, con ficha completa (ejemplos y audio). Pro vende el estudio, no la consulta** | La consulta atrae usuarios y posiciona en buscadores; el valor de pago está en estudiar con calendario y, después, en la pronunciación | Limitar la ficha por plan | Firme | R-CON-09, R-DER-05 |
| D-11 | El contenido tiene dos capas con estado propio: la base de la palabra (acepciones y ejemplos en chino) y el contenido por idioma. Cada una tiene versiones; solo una publicada | Corrige el hueco detectado en la revisión técnica: las oraciones generadas no tenían estado de borrador | Un solo estado por palabra e idioma | Firme | R-CON-04, R-CON-05 |
| D-12 | Todo contenido, generado, importado o escrito a mano, pasa por borrador, validación automática y revisión humana antes de publicarse | Un error visto por un profesor cuesta la recomendación | Publicar lo importado sin revisar | Firme | R-CON-06, R-CON-07 |
| D-13 | El contenido se genera con comandos fuera de la aplicación y se revisa en el panel de administración de Django. No se construye un panel propio ni generación desde la interfaz | Ya funciona, y el editor es una sola persona | Panel de administración a medida | Firme | — |
| D-14 | Una palabra es una sola tarjeta con todas sus acepciones. El progreso pertenece a la palabra, no a cada acepción | Partir las palabras polisémicas en varias tarjetas confunde al estudiante | Una tarjeta por acepción | Firme | R-REP-01 |

## 3. Estudio

| ID | Decisión | Por qué | Descartado | Estado | Reglas |
|---|---|---|---|---|---|
| D-15 | Calificación con dos botones: "Recordé" y "No recordé". A FSRS solo llegan "Good" y "Again" | Menos dudas al calificar; la documentación de FSRS lo considera válido | Cuatro botones | Firme | R-REP-03 |
| D-16 | **"Ya la sé" no se envía a FSRS como "Easy".** Se registra como "Recordé" con una marca, no consume el límite de nuevas, y su primera comprobación se fija entre 3 y 21 días después, repartida | Ver la sección 6 | Mapear a "Easy"; no crear estado y esconder la palabra | **Sustituida** por D-42 | R-REP-03, R-REP-14 |
| D-17 | Tres habilidades con estado de repaso propio: lectura y escucha por palabra, escritura por carácter. Las tres con FSRS | La escucha es la mitad del examen en HSK 1–2 y saber leer una palabra no implica reconocerla al oído | Escucha como ejercicio sin calendario; algoritmo propio para escritura | Firme | R-REP-01, R-REP-02, R-REP-07 |
| D-18 | En escritura solo el modo de memoria cambia el calendario. La calificación la decide el sistema: "Recordé" si no hubo pista y hubo como máximo 2 trazos errados. El umbral es configurable y se ajustará con datos | Evita que el estudiante se autocalifique con indulgencia y da un criterio comprobable | Autocalificación; que el modo con guía cuente | Firme | R-ESC-02, R-ESC-03, R-ESC-04 |
| D-19 | Solo la primera respuesta del día a una tarjeta cambia su estado; las reapariciones tras un fallo son refuerzo | Hace el comportamiento determinista y fácil de probar | Pasos de reaprendizaje de FSRS dentro de la sesión | Firme (22 nov 2026) | R-REP-05 |
| D-20 | El repaso libre no cambia estados, límites, día activo ni racha | Permite repasar antes del examen sin dañar el calendario | — | Firme | R-REP-10 |
| D-21 | Una sesión tiene una sola habilidad. "Estudiar hoy" encadena sesiones | Mezclar habilidades complica la cola, la reanudación y las métricas | Sesión combinada de lectura y escritura | Firme (22 nov 2026) | R-SES-12 |
| D-22 | Mazos simples: del sistema o propios. No hay listas ni carpetas que contengan mazos | Complejidad sin demanda comprobada | Jerarquía de listas y mazos del curso | Firme | R-MAZ-01 |

| D-47 | **En escritura el estudiante elige el modo de cada sesión**: con guía o de memoria. Solo el de memoria cambia el calendario (D-18) | Quien está empezando necesita practicar el trazo sin presión, y quien ya lo domina quiere ir directo a la memoria | Modo impuesto por el sistema | Firme (fundador, 22 nov 2026) | R-ESC-06, R-ESC-09 |
| D-48 | **Escritura solo de la lista de escritura del sílabo** (书写字: 100 caracteres en HSK 1–2 y 150 por nivel de HSK 3 a 6). Lo demás se lee, pero no se pide escribir. Los 100 de HSK 1–2 se reparten en 50 y 50: a HSK 1 van el núcleo de principiante (números, personas, saludos, familia, tamaño y lugar, tiempo) y los más frecuentes entre los que aparecen en palabras de HSK 1 | El examen pide escribir muchos menos caracteres de los que pide leer; pedirlos todos cansa y no rinde | Escribir todos los caracteres de cada palabra | Firme (fundador, 22 nov 2026) | R-ESC-10 |
| D-49 | **Mazos del sistema por tema** dentro de cada nivel, ordenados por utilidad; los temas grandes se parten con el tamaño de D-43. Sustituye el criterio de orden del sílabo de D-43; el tamaño se mantiene | Agrupar por tema ayuda a memorizar y da sentido a cada mazo | Orden del sílabo; frecuencia; lecciones de un libro (queda para mazos de clase en V2) | Firme (fundador, 22 nov 2026): 11 temas y 46 subtemas, reglas de clasificación y de tamaño en `08-contenido.md` §7 y en `content/pipeline/data/themes.json` | R-MAZ-02 |
| D-38 | Los mazos del sistema son tramos de 25 palabras consecutivas en el orden del sílabo, con nombre por clave ("HSK 1 · Parte 3") | Cero trabajo editorial y cero nombres que traducir | Mazos temáticos con nombre redactado | **Sustituida** por D-43 | R-MAZ-02 |
| D-39 | Una sesión tiene como máximo 50 tarjetas; el resto queda pendiente | Sesiones que caben en un rato de teléfono y colas guardadas pequeñas | Sesión sin tope | Firme (22 nov 2026) | R-SES-02 |
| D-40 | En "todos los pendientes", las palabras nuevas salen de los mazos del sistema en orden de nivel y de mazo | "Estudiar hoy" debe poder enseñar palabras nuevas sin que el estudiante elija mazo | Que "todos los pendientes" no incluya nuevas | Firme (22 nov 2026) | R-REP-08 |
| D-42 | **No hay "Ya la sé".** Una tarjeta nueva ofrece lo mismo que cualquier otra: "Recordé" y "No recordé". Quien ya conoce una palabra responde "Recordé" y FSRS la espacia. Sustituye a D-16 | Un botón menos, ninguna marca especial en el historial y un caso menos que probar; desaparece el riesgo de inflar el progreso | "Ya la sé" como "Recordé" marcado (D-16) | Firme (fundador, 22 nov 2026) | R-REP-03, R-REP-14 (retirada) |
| D-43 | **Mazos del sistema que crecen con el nivel.** Tramos consecutivos en el orden del sílabo; el tamaño es un parámetro por nivel que empieza en 25 en los niveles cortos y sube de 5 en 5 o de 10 en 10 en los largos, para que ningún nivel tenga demasiados mazos. El último mazo de un nivel se queda con el resto. Sustituye a D-38 | Con 25 fijo, HSK 6 tendría 72 mazos; con el tamaño creciente ningún nivel pasa de unos 30 | Tamaño fijo de 25 (D-38) | Firme el criterio (fundador, 22 nov 2026); los valores son parámetros ajustables | R-MAZ-02 |

## 4. Guardado, sesiones y hábito

| ID | Decisión | Por qué | Descartado | Estado | Reglas |
|---|---|---|---|---|---|
| D-23 | Cada respuesta se guarda en el servidor con un identificador único de cliente y se aplica una sola vez. Lo no enviado se conserva en el dispositivo y se reenvía solo | En el MVP anterior los usuarios abandonaban al perder el progreso de una sesión | Guardar al terminar la sesión; modo sin conexión completo | Firme | R-SES-03, R-SES-04 |
| D-24 | Reanudación exacta: se continúa en la primera tarjeta sin responder y no se recalcula la cola. Lo ya repasado por otra vía se salta | Es lo que el usuario entiende por "donde quedé" | Recalcular la cola al reanudar (regla de los Workshops) | Firme | R-SES-06 |
| D-25 | En escritura la unidad de guardado es el carácter. Un carácter a medias se reinicia limpio | Guardar por trazo complica contar trazos errados al reanudar y no resuelve el abandono | Guardar por trazo | Firme | R-ESC-07 |
| D-26 | **Un día sin nada pendiente no rompe la racha.** Cada día cerrado es activo, exento o fallado; la racha se rompe solo en un día fallado | Con pocas palabras y FSRS habrá días sin tarjetas; castigarlos sería injusto | Racha estricta por días consecutivos de estudio | Firme | R-PRO-03, R-PRO-04 |
| D-27 | El estado de cada día se guarda al cerrarse y no se recalcula. La racha deja de ser un valor puramente derivado de las respuestas | Lo que estaba pendiente un día pasado no se puede reconstruir después | Calcular la racha siempre al vuelo | Firme (consecuencia de D-26) | R-PRO-09 |
| D-28 | El día del estudiante empieza a las 4:00 a. m. de su zona horaria | Quien estudia pasada la medianoche no pierde el día | Corte a medianoche | Firme (22 nov 2026) | R-PRO-01 |
| D-44 | El buzón de respuestas sin confirmar vive en `localStorage` en V1, no en IndexedDB | Las respuestas son pocas y pequeñas; `localStorage` es síncrono, sobrevive a recargar y cerrar, y no añade una dependencia. Si el volumen crece se pasa a IndexedDB sin cambiar el protocolo | IndexedDB desde el primer día | Firme (22 nov 2026) | R-SES-04, `09-arquitectura` |

## 5. Cuentas, planes y datos

| ID | Decisión | Por qué | Descartado | Estado | Reglas |
|---|---|---|---|---|---|
| D-29 | En V1 el registro es abierto por un enlace no publicado, con un código de cohorte opcional en el enlace. No hay sistema de invitaciones | Ver la sección 7 | Códigos de invitación; cuentas creadas a mano | **Sustituida** por D-46 | R-CTA-10 |
| D-30 | La verificación del correo no bloquea el estudio; solo es requisito para funciones sensibles | Estudiar en el primer minuto importa más que el correo verificado | Verificación obligatoria antes de usar (regla de los Workshops) | Firme | R-CTA-06 |
| D-31 | El invitado (probar sin cuenta) se construye en V2, limitado a lectura y escucha de HSK 1. El modelo de cuentas lo admite desde V1 | En V1 los usuarios llegan por una clase y no necesitan prueba previa | Invitado con escritura | Firme | R-CTA-02, R-CTA-03 |
| D-32 | Autenticación propia en Django. PostgreSQL y servicios de fondo en Railway, interfaz en Vercel, archivos en Cloudflare R2. Supabase queda descartado | Ya está construido así; una sola plataforma de servidor | Supabase para base de datos, autenticación y archivos | Firme | `09-arquitectura` |
| D-33 | Planes: **Free** (HSK 1 y 2 completos y hasta 10 mazos propios) y **Pro** (HSK 1–6 y pronunciación con cuota). No hay plan Max | Dos planes bastan mientras no haya usuarios de pago | Tercer plan | Firme | R-DER-05 |
| D-34 | Los derechos de acceso se modelan desde V1 como datos (planes, concesiones, límites y cuotas) y toda comprobación pasa por un único punto. El cobro se construye en V3 | Añadir derechos a un producto ya construido es la deuda más cara de un modelo de pago | Comprobaciones de plan repartidas por el código | Firme | R-DER-01 a R-DER-04 |
| D-35 | Forma de cobro: recomendado un pase Pro por tiempo, de pago único y sin renovación; la suscripción se añade después si los datos lo justifican | Cumple la definición de Pro sin la maquinaria de suscripciones y no cambia el modelo | — | **Abierta** | `05-mapa`, sección 7 |
| D-45 | Se adelanta el acceso con Google (HU-E02-03) de V2 a V1b | Hay equipo para construirlo y reduce la fricción del registro en clase | Esperar a la compuerta de V2 (D-05) | Firme (fundador, 22 nov 2026) | R-CTA-07 |
| D-46 | El registro está **enlazado desde la página de inicio**. La cohorte sigue llegando por el enlace que se da a cada profesor y `signup_mode` sigue cerrando el registro sin desplegar. Sustituye a D-29 | La página de inicio sin registro visible confunde a quien llega por ella | Registro en una dirección no publicada (D-29) | Firme (fundador, 22 nov 2026) | R-CTA-10 |
| D-36 | Solo se admiten mayores de edad en la primera versión | Evita la autorización de representantes mientras no haya asesoría legal | Admitir menores | Firme, con validación legal pendiente | R-DAT-03 |
| D-41 | La analítica se guarda en una tabla propia de PostgreSQL, escrita en la misma transacción que el hecho que mide. Sin servicios de terceros en V1 | Un proveedor menos que declarar en la política de datos, y eventos que no pueden contradecir a los datos | Servicio externo de analítica | Firme (22 nov 2026) | R-DAT-07, `07-eventos` |
| D-37 | **Preparación de voz desde V1, sin interfaz:** consentimiento específico e independiente para grabar la voz; almacenamiento privado y cifrado con borrado automático a los 30 días; borrado al revocar; cuota de uso, interruptor global y tope de gasto; eventos de analítica sin audio | La voz es dato sensible según la Ley 1581 de 2012; diseñarlo después obligaría a rehacer consentimientos y almacenamiento | Añadirlo todo en V4 | Firme, con validación legal pendiente | R-DAT-02, R-DAT-08, R-DER-09, R-DER-10 |

## 6. "Ya la sé" (D-16, sustituida por D-42)

D-16 proponía registrar "Ya la sé" como un "Recordé" marcado, sin consumir el límite de nuevas y con la primera comprobación repartida entre 3 y 21 días, para no mandar "Easy" a FSRS. El fundador decidió el 22 nov 2026 no tener el botón (D-42). Lo que sigue en pie de aquel análisis: a FSRS solo llegan "Good" y "Again" (D-15), y nunca "Easy". Quien ya conoce una palabra la responde "Recordé" en su primera aparición; FSRS le da la estabilidad inicial de "Good" y la alarga en cuanto la vuelve a recordar.

## 7. Registro en V1: lo más simple (D-29)

Basta un **registro abierto en una dirección que no se publica**, sin códigos de invitación. Hace falta solo una cosa más: saber de qué clase viene cada cuenta, porque el experimento mide por clase.

| Elemento | Cómo |
|---|---|
| Acceso al registro | Dirección no enlazada desde ningún sitio; las páginas piden a los buscadores no indexarlas |
| Procedencia | El enlace que das a cada profesor lleva un código de cohorte; se guarda en la cuenta y acompaña a sus eventos |
| Cierre de emergencia | Un interruptor cierra el registro sin desplegar |
| Lo que no hace falta | Códigos de un solo uso, listas de espera, aprobación manual |

Un enlace no publicado no es un control de acceso: quien lo reciba reenviado podrá registrarse. Para una prueba con una o dos clases es aceptable; esas cuentas quedan sin cohorte o con la de quien lo compartió.

## 8. Decisiones abiertas

Las que bloqueaban V1a se cerraron el 22 nov 2026: D-19, D-21, D-28, D-29, D-39 y D-40 quedan firmes tal como estaban redactadas; D-16 y D-38 quedan sustituidas por D-42 y D-43.

| ID | Qué falta | Bloquea |
|---|---|---|
| D-35 | Elegir forma de cobro y verificar qué pasarelas operan para un vendedor en Colombia | V3 |
| — | Validación legal de D-36 y D-37, y de qué prueba de autorización se conserva al eliminar una cuenta | Antes de abrir al público (V2) |
