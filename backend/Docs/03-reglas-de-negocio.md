# 03 · Reglas de negocio

**Para qué sirve:** es el único lugar donde se escribe una regla. Las historias, las pruebas y el código la citan por su ID y no la repiten. Si una historia necesita una regla que no está aquí, primero se agrega aquí.

**Tope de extensión:** 350 líneas. **Estado:** tercera revisión (22 nov 2026); cierra los supuestos de V1a y retira "Ya la sé".

**Convenciones**

- ID: `R-<área>-<nn>`. Un ID nunca se reutiliza ni se renumera; una regla eliminada queda como "retirada".
- Esta numeración **reemplaza** a las RN de los Workshops. No hay equivalencia mantenida.
- Los términos en cursiva están definidos en `02-glosario.md`.
- **SUPUESTO ABIERTO**: lo propongo yo y el fundador aún no lo ha confirmado. **PROPUESTA**: respuesta a una cuestión que el fundador pidió resolver. **CONFIRMADO**: fue supuesto y el fundador lo aceptó. **LEGAL**: requiere validación con asesoría legal antes de publicar.
- El estado de todos los supuestos está en la sección 12.
- Los valores numéricos ajustables están en la sección 11 y se citan por nombre.

| Área | Prefijo | Sección |
|---|---|---|
| Cuentas y acceso | `R-CTA` | 1 |
| Idioma | `R-IDI` | 2 |
| Contenido y diccionario | `R-CON` | 3 |
| Mazos | `R-MAZ` | 4 |
| Repaso espaciado | `R-REP` | 5 |
| Escritura | `R-ESC` | 6 |
| Sesiones, guardado y reanudación | `R-SES` | 7 |
| Progreso y hábito | `R-PRO` | 8 |
| Derechos de acceso, límites y cuotas | `R-DER` | 9 |
| Datos personales y voz | `R-DAT` | 10 |

---

## 1. Cuentas y acceso

| ID | Regla |
|---|---|
| R-CTA-01 | Hay un solo rol de usuario final, *estudiante*. *Editor* y *dueño* son permisos de personal interno. El *visitante* no se almacena. |
| R-CTA-02 | Un *invitado* tiene una cuenta anónima sin datos personales, ligada a su navegador. Puede estudiar en lectura y escucha los mazos del sistema de HSK 1; no puede crear mazos, escribir caracteres ni cambiar preferencias. Su cuenta se borra tras `guest_ttl_days` sin actividad. **CONFIRMADO**; se construye en V2. |
| R-CTA-03 | Al registrarse, la cuenta de invitado **se convierte** en la cuenta registrada: conserva su identificador y todo su progreso. No hay copia ni fusión. |
| R-CTA-04 | Si un invitado accede a una cuenta que ya existía, el progreso de invitado se descarta, previa advertencia. No se fusiona. **SUPUESTO ABIERTO**. |
| R-CTA-05 | Para registrarse hay que aceptar expresamente la *política de datos* vigente (`R-DAT-01`) y declarar ser mayor de edad (`R-DAT-03`). Sin ambas no se crea la cuenta. |
| R-CTA-06 | La verificación del correo no bloquea el estudio. Una cuenta sin verificar no puede: recibir recordatorios, exportar sus datos, cambiar su correo, comprar ni usar funciones de voz. |
| R-CTA-07 | El acceso con Google se vincula a una cuenta existente solo si el correo coincide y Google lo declara verificado. Un correo que llega verificado por Google queda verificado. |
| R-CTA-08 | Tras `login_max_failures` intentos fallidos en `login_window_min` minutos, el acceso a esa cuenta se bloquea `login_lock_min` minutos. El mensaje no revela si el correo existe. |
| R-CTA-09 | Una cuenta suspendida no puede acceder. Sus datos se conservan y la suspensión no borra progreso ni cancela concesiones. Solo el *dueño* suspende y reactiva, con motivo registrado. |
| R-CTA-10 | El registro está abierto y enlazado desde la página de inicio (D-46); la página de registro pide a los buscadores no indexarla. No hay códigos de invitación. La dirección puede llevar un código de *cohorte*, que se guarda en la cuenta y acompaña a sus eventos para saber de qué clase viene. El interruptor `signup_mode` (`open` o `closed`) cierra el registro sin desplegar. **CONFIRMADO**. |

## 2. Idioma

| ID | Regla |
|---|---|
| R-IDI-01 | El *idioma de la interfaz* y el *idioma de estudio* son dos preferencias independientes del perfil. Cambiar uno no cambia el otro. |
| R-IDI-02 | Los idiomas son datos, no código: una tabla de idiomas con dos interruptores, *activo para estudio* y *activo para interfaz*. Al lanzar: español activo en ambos; inglés cargado e inactivo en ambos. |
| R-IDI-03 | Ningún texto visible está escrito en el código ni en plantillas. Todo sale de una *clave de traducción*. Esto incluye mensajes de error del servidor, correos, textos de accesibilidad y unidades. |
| R-IDI-04 | El catálogo de interfaz en inglés se mantiene completo desde el primer día aunque esté inactivo. Una clave sin traducción en algún idioma cargado hace fallar la integración continua. |
| R-IDI-05 | Cada palabra tiene un *contenido por idioma* por cada idioma, con su propio *estado editorial*. Publicar o retirar el contenido de un idioma no afecta al de otro. |
| R-IDI-06 | El estudiante ve los significados y traducciones de su idioma de estudio y de ningún otro. Si la palabra no está publicada en ese idioma, la ve *en revisión* (`R-CON-08`), aunque esté publicada en otro. |
| R-IDI-07 | La búsqueda por significado busca solo en el idioma de estudio, con índice y normalización propios de ese idioma (tildes, mayúsculas, raíces). |
| R-IDI-08 | Un *audio* se identifica por el texto, el idioma hablado y la *voz*. El esquema no supone "un audio por palabra" ni un único idioma hablado. Hoy solo se genera chino. |
| R-IDI-09 | Todo nombre que el sistema muestra y que no escribe el usuario (mazos del sistema, niveles, categorías gramaticales, planes, política de datos, asuntos de correo) se resuelve por clave o por registro por idioma. |
| R-IDI-10 | **Criterio de facilidad.** Añadir un idioma de estudio consiste en exactamente tres pasos: (1) cargar su contenido con los mismos comandos de la tubería, (2) revisarlo y publicarlo, (3) encender sus interruptores. Debe cumplirse con **cero migraciones de esquema, cero cambios de código y cero despliegues**. |
| R-IDI-11 | Lo único que añadir un idioma sí puede requerir es trabajo editorial: traducir claves nuevas de interfaz, revisar contenido y redactar la política en ese idioma. |
| R-IDI-12 | Al cambiar de idioma de estudio, el estudiante conserva todos sus *estados de repaso*, porque pertenecen a la palabra y no a su traducción. Las palabras no publicadas en el nuevo idioma dejan de aparecer en sus colas hasta que se publiquen. |
| R-IDI-13 | Todo *evento de analítica* lleva el idioma de la interfaz y el idioma de estudio de la cuenta. |

**Pruebas que demuestran R-IDI-10** (deben existir y pasar desde la primera versión):

| Prueba | Qué demuestra |
|---|---|
| `test_add_language_without_migration` | Con un idioma ficticio `xx`: se cargan 5 palabras, se publican, se enciende el interruptor y un estudiante completa registro, búsqueda, ficha y sesión en `xx`, sin migración ni cambio de código |
| `test_i18n_no_literal_strings` | El análisis estático no encuentra textos visibles fuera de los catálogos |
| `test_i18n_catalogs_complete` | Todos los catálogos cargados tienen todas las claves |
| `test_ui_and_study_language_independent` | Interfaz en un idioma y estudio en otro funcionan a la vez |
| `test_content_status_independent_per_language` | Publicar en un idioma no hace visible el contenido de otro |
| `test_search_scoped_to_study_language` | La búsqueda por significado no devuelve coincidencias de otro idioma |
| `test_audio_keyed_by_language_and_voice` | Dos audios del mismo texto con distinta voz o idioma coexisten |
| `test_system_names_translated` | Mazos del sistema, niveles y planes cambian con el idioma de la interfaz |

## 3. Contenido y diccionario

| ID | Regla |
|---|---|
| R-CON-01 | La lista de palabras, con hanzi, pinyin, nivel y número de orden, proviene del *sílabo* de 2025 y se coteja contra el documento oficial antes de publicar un nivel. El diccionario contiene exactamente las palabras de HSK 1 a 6 del sílabo. |
| R-CON-02 | Una *glosa de terceros* nunca se muestra a un estudiante ni se incluye en exportaciones o páginas públicas. Se guarda en un campo interno con su fuente. |
| R-CON-03 | Cada palabra tiene un identificador estable que no depende de su hanzi ni de su nivel. Corregir un dato no cambia el identificador. |
| R-CON-04 | El contenido tiene dos capas, cada una con su estado editorial: la *base de la palabra* (acepciones y ejemplos en chino, común a todos los idiomas) y el *contenido por idioma*. Un contenido por idioma solo puede publicarse si la base está publicada. |
| R-CON-05 | De cada base y de cada contenido por idioma existe como máximo una *versión* publicada y un borrador. Publicar un borrador reemplaza a la versión publicada en una sola operación; el estudiante nunca ve una palabra a medio cambiar ni se queda sin contenido durante una corrección. |
| R-CON-06 | Un borrador con alguna *validación* fallida no puede publicarse. Las validaciones se vuelven a ejecutar cada vez que el borrador se edita. |
| R-CON-07 | Toda publicación registra quién publicó, cuándo y a partir de qué origen (generado, importado o manual). Todo contenido, sea cual sea su origen, pasa por borrador y revisión humana antes de publicarse. |
| R-CON-08 | **Qué muestra el diccionario.** Palabra publicada en el idioma de estudio: significados, ejemplos con traducción y audio. Palabra no publicada: solo el *dato del sílabo* y el aviso "en revisión". |
| R-CON-09 | La ficha completa del diccionario, con ejemplos y audio, es gratuita para todos los niveles y para cualquier persona. El plan limita **estudiar**, no consultar (`R-DER-05`). **CONFIRMADO**. |
| R-CON-10 | Una palabra solo entra en una cola de estudio si está publicada en el idioma de estudio del estudiante. Las no publicadas se omiten y se cuentan aparte como "en revisión". |
| R-CON-11 | **Cambios y progreso.** (a) Corregir una palabra conserva los estados de repaso. (b) Una palabra que cambia de nivel se lleva su progreso; el derecho a estudiarla se evalúa con el nivel nuevo. (c) Una palabra retirada sale de los mazos del sistema y de las colas, y deja de contar en el avance; su historial se conserva. |
| R-CON-12 | Un carácter solo se ofrece en escritura si tiene datos de trazos. Los que no los tienen se omiten y se informa cuántos. |
| R-CON-13 | Un audio se genera una sola vez por texto, idioma y voz, y se almacena. Una palabra sin audio se puede estudiar en lectura; no entra en escucha. |
| R-CON-14 | Cualquier estudiante puede enviar un *reporte de error* sobre una palabra, indicando qué elemento falla. Un reporte está abierto, resuelto o descartado. Si la resolución cambia el contenido, pasa por una versión nueva (`R-CON-05`). |
| R-CON-15 | La aplicación tiene una página de créditos con las licencias de los datos y las librerías de terceros. No se publica una versión sin ella. |
| R-CON-16 | Un nivel se muestra aunque esté incompleto, con el número de palabras publicadas sobre el total del sílabo. |

## 4. Mazos

| ID | Regla |
|---|---|
| R-MAZ-01 | Un *mazo* es del sistema o propio. No hay otros tipos ni contenedores de mazos. |
| R-MAZ-02 | Los *mazos del sistema* son de solo lectura. Cada palabra vigente del sílabo está en exactamente un mazo del sistema, que pertenece a su nivel. Cada nivel se divide en mazos de `system_deck_size` palabras consecutivas en el orden del sílabo, con un tamaño propio por nivel que crece con el nivel (D-43); el último mazo del nivel se queda con el resto. **CONFIRMADO**. Pasará a mazos por tema cuando esté construida la asignación de temas (D-49). |
| R-MAZ-03 | Un *mazo propio* pertenece a un estudiante y solo él lo ve. Su nombre tiene de 1 a 60 caracteres y no se repite entre sus mazos, sin distinguir mayúsculas. |
| R-MAZ-04 | Un mazo propio contiene solo palabras del diccionario. Una palabra aparece una vez por mazo y puede estar en varios. Admite hasta `own_deck_max_words` palabras. |
| R-MAZ-05 | El número de mazos propios que un estudiante tiene a la vez no supera su *límite* (`R-DER-05`). Se cuentan los mazos existentes, no los creados históricamente. **SUPUESTO ABIERTO** (interpretación de "hasta 10 mazos"). |
| R-MAZ-06 | Eliminar un mazo propio nunca borra estados de repaso ni historial. Si tiene una sesión en curso, se pide confirmación y la sesión se descarta. |
| R-MAZ-07 | Un mazo propio puede contener palabras que el estudiante no puede estudiar (fuera de su plan o en revisión). Se muestran como *bloqueadas* o "en revisión" y no entran en sus colas. |

## 5. Repaso espaciado

| ID | Regla |
|---|---|
| R-REP-01 | Hay tres *habilidades*: lectura y escucha, cuya unidad es la palabra, y escritura, cuya unidad es el carácter. Existe un único *estado de repaso* por estudiante, habilidad y unidad, independiente de los mazos. |
| R-REP-02 | Las tres habilidades se programan con FSRS, cada una con sus propios parámetros y su retención objetivo (`fsrs_target_retention`). El programador está detrás de una interfaz y se puede sustituir sin tocar sesiones ni progreso. |
| R-REP-03 | A FSRS solo llegan dos *calificaciones*: **Recordé** equivale a "Good" y **No recordé** a "Again". Nunca se usan "Hard" ni "Easy". Una tarjeta nueva ofrece las mismas dos calificaciones que cualquier otra; no existe "Ya la sé" (D-42). **CONFIRMADO**. |
| R-REP-04 | Una tarjeta es *nueva* si no tiene estado en esa habilidad. Está *pendiente* si su próximo repaso cae en el *día* de hoy o antes. |
| R-REP-05 | Solo la **primera respuesta del día** a una tarjeta en una sesión programada cambia su estado de repaso. Si fue "No recordé", la tarjeta reaparece como *refuerzo* en la misma sesión, tras al menos `reinforce_gap` tarjetas, hasta que se responda "Recordé"; los refuerzos se registran y no cambian el estado. **CONFIRMADO**. |
| R-REP-06 | Hay un *límite diario de nuevas* por habilidad: `new_limit_recognition` para lectura y `new_limit_writing` para escritura, ambos editables por el estudiante. El límite cuenta entre todos los mazos. |
| R-REP-07 | Una palabra es elegible en escucha desde el día siguiente a su primer "Recordé" en lectura. La escucha tiene su propio estado de repaso y no tiene límite de nuevas propio. **CONFIRMADO**. |
| R-REP-08 | Orden de una cola programada: primero las pendientes, de la más atrasada a la menos; después las nuevas, en el orden del mazo, hasta agotar el límite. En *todos los pendientes*, las nuevas salen de los mazos del sistema que el plan permite, en orden de nivel y de mazo. **CONFIRMADO**. |
| R-REP-09 | Repasar una tarjeta desde cualquier mazo actualiza su único estado y la quita de lo pendiente en todos los demás. |
| R-REP-10 | En un *repaso libre* ninguna respuesta cambia estados de repaso, límites, día activo ni racha. Se registra para analítica. |
| R-REP-11 | *Deshacer* anula solo la última respuesta de la sesión en curso y restaura exactamente el estado anterior, el límite de nuevas y la posición. |
| R-REP-12 | Una palabra está *aprendida* cuando su estabilidad en lectura es de `learned_stability_days` días o más; un carácter, cuando lo es en escritura. Es un valor derivado: puede dejar de cumplirse tras un "No recordé". |
| R-REP-13 | El historial de respuestas solo crece. Una respuesta deshecha se marca como anulada, no se borra. Es la base para optimizar FSRS más adelante. |
| R-REP-14 | **Retirada** (D-42). Regulaba el primer repaso de las palabras marcadas "Ya la sé". |

## 6. Escritura

| ID | Regla |
|---|---|
| R-ESC-01 | El estado de escritura es por carácter. Una palabra está pendiente en escritura si al menos uno de sus caracteres lo está. La sesión pide solo los caracteres pendientes o nuevos, mostrando la palabra como contexto. |
| R-ESC-02 | Hay dos modos: *con guía* y *de memoria*. Solo las respuestas de memoria en una sesión programada cambian el estado de repaso. La práctica con guía se registra y no cambia nada. |
| R-ESC-03 | En modo de memoria la calificación la decide el sistema, no el estudiante: **Recordé** si completó el carácter sin *pista* y con `writing_max_stroke_misses` *trazos errados* o menos; **No recordé** en cualquier otro caso. |
| R-ESC-04 | Cambiar `writing_max_stroke_misses` rige desde ese momento; no recalcula respuestas pasadas. Cada respuesta guarda el número de trazos errados, si hubo pista y el umbral vigente, para poder ajustarlo con datos. |
| R-ESC-05 | Un *trazo errado* es un intento que el reconocedor rechaza. Tras `auto_hint_after_misses` trazos errados seguidos en el mismo trazo, se muestra una pista automática, que cuenta como pista. |
| R-ESC-06 | El estudiante elige el modo de cada sesión de escritura: *con guía* o *de memoria* (D-47). La sesión con guía es práctica: se registra, no cambia estados de repaso, no consume el límite de nuevas ni hace el día activo (R-ESC-02, R-PRO-03). **CONFIRMADO**. |
| R-ESC-07 | La unidad de guardado en escritura es el carácter. Un carácter respondido nunca se vuelve a pedir en esa sesión, salvo como refuerzo. Si el estudiante sale a mitad de un carácter, ese carácter se reinicia limpio al volver y el intento parcial no cuenta. **CONFIRMADO**. |
| R-ESC-08 | Si un carácter aparece en varias palabras de la misma cola, se pide una sola vez. |
| R-ESC-10 | Solo se piden en escritura los caracteres de la *lista de escritura* del sílabo, cada uno desde su nivel; la lista común de HSK 1 y 2 se reparte en 50 caracteres para HSK 1 y 50 para HSK 2 (D-48). En un mazo de nivel N entran los de nivel N o inferior; en *todos los pendientes*, los de los niveles que el plan permite, en el orden de la lista. Un carácter fuera de la lista se puede practicar con guía desde la ficha, pero no tiene calendario ni cuenta en el progreso (D-48). **CONFIRMADO**. |
| R-ESC-09 | En una sesión de memoria, un carácter nuevo se presenta primero con guía, sin calificación, y enseguida de memoria; esa respuesta de memoria es su primera calificación. **PROPUESTA**. |

## 7. Sesiones, guardado y reanudación

| ID | Regla |
|---|---|
| R-SES-01 | Una *sesión* tiene un estudiante, un alcance (un mazo o *todos los pendientes*), una sola habilidad y un tipo (programada o libre). |
| R-SES-02 | La *cola* se calcula al iniciar la sesión, se guarda con su orden y no se le agregan tarjetas después. Tiene como máximo `session_max_cards` tarjetas, sin contar refuerzos; lo que no cabe sigue pendiente para la sesión siguiente. **CONFIRMADO**. |
| R-SES-03 | Cada *respuesta* viaja con un identificador único generado en el dispositivo. El servidor aplica cada identificador una sola vez: recibirlo de nuevo devuelve el mismo resultado sin repetir el efecto. Una tarjeta solo se da por respondida cuando el servidor lo confirma. |
| R-SES-04 | Las respuestas que no han podido enviarse se guardan en el dispositivo, sobreviven a recargar o cerrar la página y se reenvían solas. No es un modo sin conexión: sin red no se pueden iniciar sesiones nuevas. |
| R-SES-05 | Hay como máximo una sesión en curso por estudiante, alcance y habilidad. Al intentar abrir otra igual se ofrece *reanudar* o *descartar*. |
| R-SES-06 | **Reanudación exacta.** Reanudar continúa en la primera tarjeta sin responder, con el mismo orden. No se recalcula la cola. Las tarjetas cuyo estado ya cambió hoy por otra vía (otro mazo u otro dispositivo) se saltan y se marcan como "ya repasada". |
| R-SES-07 | Si la misma sesión está abierta en dos dispositivos, el servidor manda. Una respuesta a una tarjeta ya respondida se rechaza sin efecto y el dispositivo recibe la posición actual. |
| R-SES-08 | Una sesión termina por completarse, por descarte del estudiante o por caducar tras `session_ttl_days` sin actividad. En los tres casos, lo ya respondido es definitivo. |
| R-SES-09 | Una sesión programada sin terminar sigue siendo reanudable al cambiar el día. Cada respuesta cuenta para el día y el límite de nuevas del momento en que se da. |
| R-SES-10 | No se crea una sesión vacía. Si no hay nada que estudiar se dice por qué: nada pendiente, límite de nuevas alcanzado, contenido en revisión o nivel fuera del plan. |
| R-SES-11 | La hora del servidor es la que vale. Para una respuesta reenviada tarde se usa la hora del dispositivo solo si cae entre el inicio de la sesión y la recepción. |
| R-SES-12 | "Estudiar hoy" encadena sesiones de una habilidad cada una (lectura, luego escucha, luego escritura), y el estudiante puede saltar cualquiera. No existe la sesión de varias habilidades. **CONFIRMADO**. |

## 8. Progreso y hábito

| ID | Regla |
|---|---|
| R-PRO-01 | El *día* de un estudiante se calcula con su zona horaria y empieza a las `day_rollover_hour`:00. Una respuesta a la 1:30 a. m. pertenece al día anterior. **CONFIRMADO**. |
| R-PRO-02 | Cambiar de zona horaria rige desde el día siguiente y no modifica días activos pasados. |
| R-PRO-03 | Cada día de un estudiante queda en uno de tres estados. **Activo**: dio al menos una respuesta que cambió un estado de repaso; no cuentan el repaso libre, la escritura con guía ni los refuerzos. **Exento**: no fue activo y, al cerrarse, no tenía ninguna tarjeta pendiente que pudiera estudiar. **Fallado**: no fue activo y tenía al menos una pendiente. Las tarjetas nuevas no obligan: tener nuevas disponibles no convierte un día en fallado. **CONFIRMADO** (decisión 1 del fundador). |
| R-PRO-04 | La *racha* actual es el número de días activos desde el último día fallado. Un día exento no la rompe ni la aumenta. El día en curso no cuenta como fallado mientras no se cierre. La racha máxima es la mayor alcanzada. |
| R-PRO-05 | Los conteos de progreso cuentan cada palabra y cada carácter una sola vez, sin importar en cuántos mazos esté, y solo contenido vigente en el sílabo. |
| R-PRO-06 | El avance de un nivel es el número de palabras aprendidas de ese nivel sobre el total del sílabo para ese nivel. Junto a él se muestra cuántas están publicadas. |
| R-PRO-07 | La *meta de examen* es opcional: nivel y fecha. El sistema sugiere cuántas palabras nuevas al día hacen falta para llegar; la sugerencia es informativa y no altera FSRS ni el límite, que el estudiante cambia si quiere. Si el ritmo necesario supera `new_limit_max`, se avisa de que la meta no es alcanzable. |
| R-PRO-08 | Un *recordatorio* exige correo verificado y consentimiento propio. Se envía como máximo uno al día, a la hora elegida (por defecto `reminder_default_hour`), solo si el día aún no es activo y hay algo pendiente, y cada correo permite darse de baja en un paso. |
| R-PRO-09 | El estado de un día se fija una sola vez, al cerrarse, y no se recalcula, porque lo que estaba pendiente en un día pasado no se puede reconstruir después. "Que pudiera estudiar" se evalúa con el plan y el idioma de estudio vigentes en ese cierre. La racha se deriva de esos estados y nunca se edita a mano. |

## 9. Derechos de acceso, límites y cuotas

| ID | Regla |
|---|---|
| R-DER-01 | Toda decisión de "¿puede esta cuenta hacer esto?" pasa por un único punto del servidor. La interfaz lo consulta para mostrar u ocultar, pero el servidor decide siempre. |
| R-DER-02 | Lo que se puede permitir se describe como *capacidades* con nombre, de tres clases: de acceso (sí o no, por ejemplo `study.level.3`), de *límite* (`decks.own.max`) y de *cuota* (`pronunciation.assess`). |
| R-DER-03 | Un *plan* es un conjunto de capacidades con sus valores, guardado como dato y versionado. Cambiar lo que incluye un plan no requiere código. |
| R-DER-04 | Una cuenta obtiene derechos solo mediante *concesiones*. Cada una tiene origen (plan por defecto, compra, promoción o manual), alcance (un plan entero o capacidades sueltas), inicio y fin; sin fin es perpetua. Los derechos vigentes son la unión de las concesiones activas; ante dos valores de un mismo límite o cuota, rige el mayor. |
| R-DER-05 | **Free** (concesión por defecto de toda cuenta registrada): estudiar HSK 1 y 2 en las tres habilidades, y hasta `free_own_decks` mazos propios. **Pro**: estudiar HSK 1 a 6, mazos propios sin límite comercial (tope técnico `own_decks_hard_cap`) y evaluación de pronunciación con cuota. El diccionario no depende del plan (`R-CON-09`). |
| R-DER-06 | El *invitado* tiene los derechos de `R-CTA-02`, que son un subconjunto de Free. |
| R-DER-07 | Un límite se comprueba al crear. Bajar de plan nunca borra nada: los objetos que exceden el límite se conservan y siguen siendo utilizables; solo se impide crear más. **SUPUESTO ABIERTO**. |
| R-DER-08 | Al perder el derecho a estudiar un nivel, sus estados de repaso e historial se conservan y siguen visibles en el progreso; sus tarjetas dejan de entrar en las colas. Al recuperarlo, vuelven como pendientes. |
| R-DER-09 | Una *cuota* tiene capacidad, cantidad y periodo (día, mes o sin renovación). Cada uso se anota como *consumo* con identificador único; el descuento es atómico y no se repite ante un reintento. Si el servicio externo falla, el consumo se revierte. |
| R-DER-10 | Toda función con costo variable tiene, además de la cuota por cuenta, un interruptor global y un tope de gasto mensual del producto. Al alcanzarlo la función se pausa para todos, con aviso, y el resto del producto sigue funcionando. |
| R-DER-11 | Lo que el plan no incluye se muestra *bloqueado*, con el plan que lo desbloquea. No se oculta que existe. |
| R-DER-12 | Una concesión manual solo la crea el dueño, con motivo, y queda en el *registro de auditoría*. |
| R-DER-13 | El efecto de una concesión nueva es inmediato. Si se usa caché de derechos, se invalida al crear, modificar o vencer una concesión. |
| R-DER-14 | Lo que una cuenta tuvo gratis al registrarse no pasa a ser de pago para esa cuenta sin aviso previo de `plan_change_notice_days` días. **SUPUESTO ABIERTO**. |

## 10. Datos personales y voz

| ID | Regla |
|---|---|
| R-DAT-01 | La *política de datos* es versionada y existe en cada idioma de interfaz activo. Cada aceptación guarda versión y fecha. Si hay una versión nueva, se pide aceptarla en el siguiente acceso antes de continuar. |
| R-DAT-02 | Hay un *consentimiento* por *finalidad*, independiente y revocable: `general` (necesario para tener cuenta), `reminder_email` y `voice_recording`. Ninguno opcional viene marcado por defecto ni se agrupa con otro. |
| R-DAT-03 | Solo se admiten mayores de edad. Si se detecta que una cuenta es de un menor, se cierra y sus datos se eliminan. **LEGAL**. |
| R-DAT-04 | El titular puede ver y exportar todos sus datos, gratis, en un formato legible por máquina, con correo verificado. |
| R-DAT-05 | El titular puede corregir sus datos de perfil en cualquier momento. |
| R-DAT-06 | Eliminar la cuenta borra o anonimiza de forma irreversible: perfil, progreso, historial, mazos, grabaciones y concesiones. Los registros de auditoría y los eventos de analítica que se conserven quedan sin vínculo con la persona. Las copias de seguridad caducan en `backup_retention_days` días como máximo. Qué prueba de la autorización se conserva y por cuánto tiempo: **LEGAL**. |
| R-DAT-07 | Un evento de analítica nunca contiene nombre, correo, texto libre ni audio; identifica a la cuenta con un seudónimo. |
| R-DAT-08 | **Voz** (se prepara ahora; se usa cuando exista la pronunciación). Una *grabación de voz* solo se captura con el consentimiento `voice_recording` vigente. Se guarda en almacenamiento privado, cifrada y sin dirección pública; se borra automáticamente a los `voice_retention_days` días; el titular puede borrar cualquiera cuando quiera. Revocar el consentimiento desactiva la función y borra todas sus grabaciones en `voice_revocation_purge_days` días como máximo. Solo se envía al proveedor externo para evaluarla, y ese proveedor figura en la política. **LEGAL** (dato sensible según la Ley 1581 de 2012). |
| R-DAT-09 | Existe un canal de consultas y reclamos. Cada solicitud se registra con su fecha de recepción y de respuesta; plazos de `data_query_days` y `data_claim_days` días hábiles. |
| R-DAT-10 | Toda acción del editor o del dueño sobre contenido, cuentas o concesiones queda en el registro de auditoría con autor, fecha y motivo. |
| R-DAT-11 | La política nombra a todos los proveedores que tratan datos personales y el país donde lo hacen. **LEGAL**. |

## 11. Parámetros ajustables

Valores iniciales. Viven en configuración, no en el código, y cambiarlos queda en el registro de auditoría.

| Parámetro | Valor inicial | Regla |
|---|---|---|
| `guest_ttl_days` | 30 | R-CTA-02 |
| `signup_mode` | `open` | R-CTA-10 |
| `login_max_failures` / `login_window_min` / `login_lock_min` | 5 / 15 / 15 | R-CTA-08 |
| `system_deck_size` (por nivel) | HSK 1: 25; HSK 2: 25; HSK 3: 30; HSK 4: 40; HSK 5: 50; HSK 6: 60 (12, 8, 17, 25, 32 y 30 mazos) | R-MAZ-02 |
| `session_max_cards` | 50 | R-SES-02 |
| `own_deck_max_words` | 500 | R-MAZ-04 |
| `free_own_decks` | 10 | R-DER-05 |
| `own_decks_hard_cap` | 200 | R-DER-05 |
| `fsrs_target_retention` | 0,90 en las tres habilidades | R-REP-02 |
| `reinforce_gap` | 3 | R-REP-05 |
| `new_limit_recognition` (rango) | 10 (0 a 50) | R-REP-06 |
| `new_limit_writing` (rango) | 5 (0 a 30) | R-REP-06 |
| `new_limit_max` | 50 | R-PRO-07 |
| `learned_stability_days` | 21 | R-REP-12 |
| `writing_max_stroke_misses` | 2 | R-ESC-03 |
| `auto_hint_after_misses` | 3 | R-ESC-05 |
| `session_ttl_days` | 7 | R-SES-08 |
| `day_rollover_hour` | 4 | R-PRO-01 |
| `reminder_default_hour` | 20 | R-PRO-08 |
| `plan_change_notice_days` | 30 | R-DER-14 |
| `backup_retention_days` | 30 | R-DAT-06 |
| `voice_retention_days` | 30 | R-DAT-08 |
| `voice_revocation_purge_days` | 7 | R-DAT-08 |
| `data_query_days` / `data_claim_days` | 10 / 15 | R-DAT-09 |
| `example_max_chars` (por nivel) | HSK 1: 12; HSK 2: 14; HSK 3: 16; HSK 4: 18; HSK 5: 20; HSK 6: 22. **PROPUESTA** | R-CON-06 (`example_length`) |
| `example_level_tolerance` (por nivel) | HSK 1: 1; HSK 2: 1; HSK 3: 1; HSK 4: 1; HSK 5: 1; HSK 6: 1. **PROPUESTA** | R-CON-06 (`example_level`) |
| `examples_max_similarity` | 0,75 | R-CON-06 (`examples_distinct`) |
| `audio_voice` | sin definir hasta elegir proveedor | R-CON-13 |

## 12. Estado de supuestos y propuestas

Tras las decisiones del fundador del 15 y el 22 nov 2026. "Bloquea" indica el primer corte al que afecta.

| Regla | Tema | Estado | Bloquea |
|---|---|---|---|
| R-CTA-02 | Alcance del invitado | Confirmado | — |
| R-CON-09 | Diccionario gratuito en todos los niveles | Confirmado | — |
| R-REP-07 | Escucha con calendario propio | Confirmado | — |
| R-ESC-07 | Guardado de escritura por carácter | Confirmado | — |
| R-PRO-03 | Día exento que no rompe la racha | Confirmado | — |
| R-REP-03 | Solo dos calificaciones; sin "Ya la sé" (D-42) | Confirmado | — |
| R-REP-14 | Primer repaso de "Ya la sé" | Retirada (D-42) | — |
| R-CTA-10 | Registro abierto por enlace no publicado, con código de cohorte | Confirmado | — |
| R-MAZ-02 | Mazos del sistema con tamaño creciente por nivel (D-43) | Confirmado | — |
| R-SES-02 | Sesiones de 50 tarjetas como máximo | Confirmado | — |
| R-REP-08 | En "todos los pendientes", las nuevas salen de los mazos del sistema en orden | Confirmado | — |
| R-REP-05 | Solo la primera respuesta del día cambia el estado; lo demás es refuerzo | Confirmado | — |
| R-SES-12 | "Estudiar hoy" encadena sesiones de una habilidad | Confirmado | — |
| R-PRO-01 | El día empieza a las 4:00 a. m. | Confirmado | — |
| R-ESC-06 | El estudiante elige con guía o de memoria (D-47) | Confirmado | — |
| R-ESC-09 | En memoria, el carácter nuevo pasa antes por la guía | **Propuesta por confirmar** | V1b |
| R-CTA-04 | El progreso de invitado se descarta al acceder a una cuenta existente | **Abierto** | V2 |
| R-MAZ-05 | "10 mazos" son mazos propios existentes a la vez | **Abierto** | V2 |
| R-DER-07 | Bajar de plan no borra; solo impide crear | **Abierto** | V2 |
| R-DER-14 | Aviso previo de 30 días antes de volver de pago algo gratuito | **Abierto** | V3 |

**Consecuencia de R-PRO-03 que conviene tener presente:** un estudiante que deja de entrar pero no tiene nada pendiente conserva su racha indefinidamente. En la práctica dura poco, porque FSRS le pondrá tarjetas pendientes a los pocos días de su último repaso.
