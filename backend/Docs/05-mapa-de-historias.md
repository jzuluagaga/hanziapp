# 05 · Mapa de historias

**Para qué sirve:** muestra el recorrido completo del usuario, las épicas, las historias con su versión y las dependencias entre ellas. Es el índice de `docs/historias/`. Aquí cada historia ocupa una línea; sus criterios de aceptación, con el nombre de su prueba, van en el archivo de su épica.

**Tope de extensión:** 260 líneas. **Estado:** tercera revisión (22 nov 2026); sin "Ya la sé" y con los supuestos de V1a cerrados.

**Convenciones**

- ID de historia: `HU-E<épica>-<nn>`. No se reutiliza ni se renumera. Reemplaza a las HU de los Workshops.
- Las historias son **por resultado del usuario**, no por acción. Una historia puede tener muchos criterios.
- Tipos: **U** (usuario final), **O** (operación: el fundador como editor o dueño), **H** (habilitadora: sin pantalla propia, pero con criterios y pruebas).
- Las reglas citadas viven en `03-reglas-de-negocio.md`; los términos, en `02-glosario.md`.

---

## 1. Versiones

| Versión | Objetivo | Para quién | Nivel de detalle |
|---|---|---|---|
| **V1 · Validar** | Saber si una clase real vuelve y aprende | Tú y una o dos clases de HSK 1–2, que se registran por un enlace no publicado (`R-CTA-10`) | Historias completas |
| **V2 · Abrir** | Que cualquiera llegue, pruebe y se quede sin ayuda tuya | Público hispanohablante | Esquema; se detalla al pasar la compuerta |
| **V3 · Cobrar** | Primer ingreso | Estudiantes de HSK 3 en adelante | Esquema |
| **V4 · Pronunciación** | Evaluación de voz con un servicio externo | Plan Pro | Esquema |

**Primer corte usable (V1a).** V1 se entrega en dos cortes. **V1a** (23 historias) es lo mínimo para poner el producto en manos de una clase y empezar a medir: contenido publicado, cuenta, lectura, escucha, guardado y reanudación, racha y tablero de retención. **V1b** (12 historias) se construye mientras V1a ya está en uso: escritura, diccionario, progreso, perfil, eliminación de cuenta y corrección de contenido.

Durante V1a se atiende a mano lo que V1b automatiza: una solicitud de eliminación de cuenta se resuelve por correo en el plazo de `R-DAT-09`; un error de contenido se corrige republicando la palabra; los avisos de error llegan por un enlace de correo visible en la aplicación.

**Compuerta entre V1 y V2.** V2 no se detalla ni se construye hasta medir V1 con una clase durante cuatro semanas (experimentos 1 y 2 de `EVALUACION-PRODUCTO.md`):

| Resultado en la semana 4 | Qué se hace |
|---|---|
| Vuelve el 35 % o más de quienes hicieron una primera sesión | Seguir con V2 |
| Entre 15 % y 35 % | Entrevistar a quienes se fueron, cambiar una sola cosa y repetir |
| Menos de 15 % en dos clases distintas | Parar y replantear antes de escribir más |

**Fuera del producto** (no hay épica): cursos y rol de profesor, simulacros de examen propios, diccionario más allá de HSK 1–6, aplicación nativa, modo sin conexión.

## 2. Recorrido del usuario

```
Descubrir → Empezar → Estudiar hoy → Escuchar → Escribir → Explorar → Organizar → Ver avance → Mi cuenta → Mi plan
   E01        E02        E03          E04        E05        E07        E08         E09          E10       E11·E12
                          └────────── E06 No perder nada (atraviesa E03, E04 y E05) ──────────┘
Debajo de todo:   E00 Cimientos   ·   E13 Operar el contenido   ·   E14 Operar el producto
Más adelante:     E15 Pronunciación
```

## 3. Épicas e historias

### E00 · Cimientos
Lo que debe existir antes de la primera pantalla para no pagar deuda después.

| ID | Tipo | Historia | Resultado | Versión | Reglas |
|---|---|---|---|---|---|
| HU-E00-01 | H | Respuestas que se aplican una sola vez | Reintentar un envío nunca duplica un repaso ni un consumo | V1a | R-SES-03, R-SES-04, R-DER-09 |
| HU-E00-02 | H | Analítica desde el primer día | Cada historia emite eventos con los que se calculan retención y aprendizaje | V1a | R-DAT-07, R-IDI-13 |
| HU-E00-03 | H | Listo para un segundo idioma | Añadir inglés es cargar, publicar y encender | V1a | R-IDI-02, R-IDI-03, R-IDI-04, R-IDI-09, R-IDI-10, R-IDI-11 |
| HU-E00-04 | H | Operación segura | Despliegue repetible, copia restaurada en una prueba real, interruptores y página de créditos | V1a | R-DAT-06, R-DER-10, R-CON-15 |

### E01 · Descubrir y probar
| ID | Tipo | Historia | Resultado | Versión | Reglas |
|---|---|---|---|---|---|
| HU-E01-01 | U | Entender la propuesta | En la página de inicio sé qué es, para quién y qué es gratis | V2 | R-IDI-03, R-DER-11 |
| HU-E01-02 | U | Consultar un nivel sin cuenta | Veo el vocabulario de un nivel y la ficha de una palabra en páginas públicas | V2 | R-CON-08, R-CON-09, R-CON-16 |
| HU-E01-03 | U | Probar sin registrarme | Hago una sesión real como invitado | V2 | R-CTA-02, R-DER-06 |

### E02 · Crear cuenta y empezar
| ID | Tipo | Historia | Resultado | Versión | Reglas |
|---|---|---|---|---|---|
| HU-E02-01 | U | Crear mi cuenta | Me registro con correo aceptando la política; en V2, conservo lo hecho como invitado | V1a | R-CTA-05, R-CTA-10, R-DAT-01, R-DAT-02, R-DAT-03, R-CTA-03, R-CTA-04 |
| HU-E02-02 | U | Acceder y recuperar mi contraseña | Entro, salgo y recupero el acceso sin ayuda | V1a | R-CTA-01, R-CTA-08, R-CTA-09 |
| HU-E02-03 | U | Entrar con Google | Accedo sin crear contraseña | V2 | R-CTA-07 |
| HU-E02-04 | U | Verificar mi correo sin que me frene | Estudio desde el primer minuto y verifico cuando quiera | V2 | R-CTA-06 |
| HU-E02-05 | U | Empezar en mi nivel | Digo mi nivel, marco lo que ya sé y, si quiero, mi fecha de examen | V2 | R-REP-03, R-PRO-07 |

### E03 · Estudiar hoy (el núcleo)
| ID | Tipo | Historia | Resultado | Versión | Reglas |
|---|---|---|---|---|---|
| HU-E03-01 | U | Ver qué me toca hoy y empezar | Con un toque empiezo lo pendiente de un mazo o de todos | V1a | R-REP-04, R-REP-08, R-SES-01, R-SES-02, R-SES-10, R-SES-12 |
| HU-E03-02 | U | Repasar una tarjeta de lectura | Veo el hanzi, revelo pinyin y significado, y digo si recordé | V1a | R-REP-01, R-REP-02, R-REP-03, R-REP-05, R-REP-09, R-CON-10 |
| HU-E03-03 | U | Aprender palabras nuevas a mi ritmo | Recibo nuevas hasta mi límite diario, en el orden del sílabo | V1a | R-REP-06, R-REP-03, R-REP-08 |
| HU-E03-04 | U | Ver cómo me fue | Al terminar veo aciertos, fallos y qué sigue | V1a | R-SES-08, R-PRO-03 |
| HU-E03-05 | U | Deshacer mi última respuesta | Corrijo un toque equivocado | V2 | R-REP-11, R-REP-13 |
| HU-E03-06 | U | Repasar un mazo libremente | Repaso todo antes del examen sin alterar mi calendario | V2 | R-REP-10 |

### E04 · Escuchar
| ID | Tipo | Historia | Resultado | Versión | Reglas |
|---|---|---|---|---|---|
| HU-E04-01 | U | Oír la palabra y su ejemplo | En cualquier tarjeta o ficha escucho el audio cuando lo pido | V1a | R-CON-13, R-IDI-08 |
| HU-E04-02 | U | Oír y elegir | Escucho una palabra y elijo su significado, con su propio calendario | V1a | R-REP-01, R-REP-07 |

### E05 · Escribir caracteres
| ID | Tipo | Historia | Resultado | Versión | Reglas |
|---|---|---|---|---|---|
| HU-E05-01 | U | Practicar con guía | Trazo un carácter siguiendo su contorno, sin que cuente | V1b | R-ESC-02, R-ESC-06, R-CON-12 |
| HU-E05-02 | U | Escribir de memoria | Trazo sin ayuda y el sistema decide si recordé | V1b | R-ESC-01, R-ESC-03, R-ESC-04, R-ESC-08 |
| HU-E05-03 | U | Pedir una pista | Me desatasco sabiendo que la pista cuenta | V1b | R-ESC-05 |

### E06 · No perder nada
La causa de abandono del MVP anterior. Atraviesa lectura, escucha y escritura.

| ID | Tipo | Historia | Resultado | Versión | Reglas |
|---|---|---|---|---|---|
| HU-E06-01 | U | Cada respuesta queda guardada | Si se cae la red o cierro la pestaña, no pierdo ni una respuesta | V1a | R-SES-03, R-SES-04, R-SES-11 |
| HU-E06-02 | U | Reanudar donde quedé, o descartar | Vuelvo a la tarjeta o al carácter exacto; o cierro la sesión conservando lo hecho | V1a | R-SES-05, R-SES-06, R-SES-08, R-SES-09, R-ESC-07 |
| HU-E06-03 | U | Seguir en otro dispositivo | Empiezo en el computador y termino en el teléfono | V1a | R-SES-07 |

### E07 · Explorar
| ID | Tipo | Historia | Resultado | Versión | Reglas |
|---|---|---|---|---|---|
| HU-E07-01 | U | Buscar una palabra | Encuentro por hanzi, pinyin con o sin tonos, o significado; en V2, filtro por nivel | V1b | R-CON-01, R-IDI-07 |
| HU-E07-02 | U | Ver la ficha de una palabra | Veo su contenido si está publicado, o sus datos del sílabo si está en revisión | V1b | R-CON-08, R-CON-02, R-IDI-06 |
| HU-E07-03 | U | Ver cómo se traza | Veo la animación del orden de trazos de cada carácter | V1b | R-CON-12 |
| HU-E07-04 | U | Avisar de un error | Reporto un fallo desde la ficha o la tarjeta | V1b | R-CON-14 |
| HU-E07-05 | U | Guardar una palabra en un mazo | Desde la ficha la agrego a un mazo propio | V2 | R-MAZ-04, R-MAZ-07 |

### E08 · Organizar
| ID | Tipo | Historia | Resultado | Versión | Reglas |
|---|---|---|---|---|---|
| HU-E08-01 | U | Ver los mazos de cada nivel | Veo cuántas palabras tiene cada mazo, cuántas nuevas y pendientes, y qué está bloqueado | V1a | R-MAZ-01, R-MAZ-02, R-CON-16, R-DER-11 |
| HU-E08-02 | U | Tener mis propios mazos | Creo, renombro y elimino mazos dentro de mi límite | V2 | R-MAZ-03, R-MAZ-05, R-MAZ-06, R-DER-07 |
| HU-E08-03 | U | Armar un mazo | Agrego, quito y ordeno palabras | V2 | R-MAZ-04, R-MAZ-07 |

### E09 · Ver avance y mantener el hábito
| ID | Tipo | Historia | Resultado | Versión | Reglas |
|---|---|---|---|---|---|
| HU-E09-01 | U | Ver mi progreso | Veo palabras y caracteres aprendidos y mi avance por nivel | V1b | R-PRO-05, R-PRO-06, R-REP-12 |
| HU-E09-02 | U | Mantener mi racha | Veo mi racha y sé qué la mantiene | V1a | R-PRO-01, R-PRO-02, R-PRO-03, R-PRO-04, R-PRO-09 |
| HU-E09-03 | U | Estudiar hacia una fecha | Fijo nivel y fecha de examen y veo el ritmo necesario | V2 | R-PRO-07 |
| HU-E09-04 | U | Recibir un recordatorio | Un correo me avisa si hoy no he estudiado | V3 | R-PRO-08, R-CTA-06 |
| HU-E09-05 | U | Comprobar que de verdad aprendo | Una prueba corta con formato de examen sobre lo "aprendido" | V3 | (regla por escribir) |

### E10 · Mi cuenta y mis datos
| ID | Tipo | Historia | Resultado | Versión | Reglas |
|---|---|---|---|---|---|
| HU-E10-01 | U | Ajustar mi perfil | Cambio nombre, idiomas, zona horaria y límites diarios | V1b | R-IDI-01, R-IDI-12, R-PRO-02, R-REP-06, R-DAT-05 |
| HU-E10-02 | U | Controlar mis consentimientos | Leo la política, acepto versiones nuevas y doy o retiro cada consentimiento | V1a | R-DAT-01, R-DAT-02, R-DAT-08, R-DAT-11 |
| HU-E10-03 | U | Eliminar mi cuenta | Borro mi cuenta y mis datos de forma definitiva | V1b | R-DAT-06 |
| HU-E10-04 | U | Ver y llevarme mis datos | Descargo todo lo que el sistema guarda de mí | V2 | R-DAT-04 |

**Preparación de voz en V1** (dentro de HU-E10-02 y HU-E11-01, sin interfaz visible): el consentimiento `voice_recording` existe como finalidad; existen la tabla de grabaciones y la tarea de borrado por plazo, probada con datos ficticios; están definidos los eventos de analítica y la capacidad con cuota. Nada de esto se muestra al usuario hasta V4.

### E11 · Derechos de acceso
| ID | Tipo | Historia | Resultado | Versión | Reglas |
|---|---|---|---|---|---|
| HU-E11-01 | H | Motor de derechos, límites y cuotas | Un solo punto decide qué puede hacer cada cuenta, con planes y concesiones como datos | V1a | R-DER-01, R-DER-02, R-DER-03, R-DER-04, R-DER-05, R-DER-09, R-DER-13 |
| HU-E11-02 | U | Saber qué incluye mi plan | Veo qué tengo, qué está bloqueado y por qué | V2 | R-DER-05, R-DER-08, R-DER-11 |
| HU-E11-03 | O | Conceder acceso a mano | Doy Pro a un probador o a una clase, con motivo y fecha de fin | V2 | R-DER-04, R-DER-12 |

### E12 · Cobro (esquema)
| ID | Tipo | Historia | Resultado | Versión | Reglas |
|---|---|---|---|---|---|
| HU-E12-01 | U | Comprar Pro | Pago y mi acceso cambia al instante | V3 | R-DER-04, R-DER-13 |
| HU-E12-02 | U | Ver el estado de mi compra | Sé qué pagué, hasta cuándo dura y cómo cancelar o pedir reembolso | V3 | R-DER-04 |
| HU-E12-03 | U | Perder el acceso sin perder mi progreso | Al vencer conservo todo; solo dejo de estudiar lo que el plan no incluye | V3 | R-DER-07, R-DER-08, R-DER-14 |

### E13 · Operar el contenido
| ID | Tipo | Historia | Resultado | Versión | Reglas |
|---|---|---|---|---|---|
| HU-E13-01 | O | Cargar el sílabo de un nivel | Las palabras del nivel existen con sus datos del sílabo, cotejadas con el documento oficial | V1a | R-CON-01, R-CON-03 |
| HU-E13-02 | O | Generar borradores validados, con audio | Un comando deja borradores, validaciones y audio; repetirlo no duplica nada | V1a | R-CON-02, R-CON-06, R-CON-07, R-CON-13 |
| HU-E13-03 | O | Revisar y publicar | Reviso, edito y publico palabra por palabra o por lote | V1a | R-CON-04, R-CON-05, R-CON-06, R-CON-07, R-IDI-05 |
| HU-E13-04 | O | Corregir lo publicado | Cambio una palabra publicada sin que nadie pierda progreso ni vea un estado intermedio | V1b | R-CON-05, R-CON-11 |
| HU-E13-05 | O | Atender los reportes | Veo los reportes abiertos y los resuelvo o descarto | V1b | R-CON-14, R-DAT-10 |

### E14 · Operar el producto
| ID | Tipo | Historia | Resultado | Versión | Reglas |
|---|---|---|---|---|---|
| HU-E14-01 | O | Ver si vuelven y si aprenden | Un tablero con retención a 1, 7 y 28 días y aciertos por intervalo | V1a | R-DAT-07 |
| HU-E14-02 | O | Atender personas | Gestiono solicitudes de datos, soporte y suspensiones con registro | V2 | R-DAT-09, R-DAT-10, R-CTA-09 |

### E15 · Pronunciación (esquema)
| ID | Tipo | Historia | Resultado | Versión | Reglas |
|---|---|---|---|---|---|
| HU-E15-01 | U | Practicar mi pronunciación | Autorizo grabar mi voz, grabo y recibo una evaluación dentro de mi cuota | V4 | R-DAT-08, R-DER-09, R-DER-10 |
| HU-E15-02 | U | Controlar mis grabaciones | Las escucho, las borro y puedo retirar mi autorización | V4 | R-DAT-08 |

## 4. Resumen por versión

| Épica | V1a | V1b | V2 | V3 | V4 | Total |
|---|---|---|---|---|---|---|
| E00 Cimientos | 4 |  |  |  |  | 4 |
| E01 Descubrir y probar |  |  | 3 |  |  | 3 |
| E02 Crear cuenta y empezar | 2 |  | 3 |  |  | 5 |
| E03 Estudiar hoy | 4 |  | 2 |  |  | 6 |
| E04 Escuchar | 2 |  |  |  |  | 2 |
| E05 Escribir caracteres |  | 3 |  |  |  | 3 |
| E06 No perder nada | 3 |  |  |  |  | 3 |
| E07 Explorar |  | 4 | 1 |  |  | 5 |
| E08 Organizar | 1 |  | 2 |  |  | 3 |
| E09 Ver avance y mantener el hábito | 1 | 1 | 1 | 2 |  | 5 |
| E10 Mi cuenta y mis datos | 1 | 2 | 1 |  |  | 4 |
| E11 Derechos de acceso | 1 |  | 2 |  |  | 3 |
| E12 Cobro |  |  |  | 3 |  | 3 |
| E13 Operar el contenido | 3 | 2 |  |  |  | 5 |
| E14 Operar el producto | 1 |  | 1 |  |  | 2 |
| E15 Pronunciación |  |  |  |  | 2 | 2 |
| **Total** | **23** | **12** | **16** | **5** | **2** | **58** |

## 5. Dependencias

Orden de construcción sugerido dentro de V1. Una historia no empieza hasta que las de su columna "Necesita" están terminadas.

| Paso | Corte | Historias | Necesita |
|---|---|---|---|
| 1 | V1a | HU-E00-03, HU-E00-04, HU-E13-01 | — |
| 2 | V1a | HU-E13-02, HU-E13-03, HU-E02-01, HU-E02-02, HU-E10-02 | Paso 1 |
| 3 | V1a | HU-E00-01, HU-E00-02, HU-E11-01 | Paso 1 |
| 4 | V1a | HU-E08-01, HU-E03-01, HU-E03-02, HU-E03-03, HU-E06-01 | Pasos 2 y 3 |
| 5 | V1a | HU-E06-02, HU-E06-03, HU-E03-04, HU-E04-01, HU-E04-02, HU-E09-02, HU-E14-01 | Paso 4 |
| | | **Primer corte usable: empieza la medición con una clase** | |
| 6 | V1b | HU-E05-01, HU-E05-02, HU-E05-03 | Paso 5 |
| 7 | V1b | HU-E07-01, HU-E07-02, HU-E07-03, HU-E07-04, HU-E13-04, HU-E13-05 | Paso 2 |
| 8 | V1b | HU-E09-01, HU-E10-01, HU-E10-03 | Pasos 3 y 4 |

**Decisiones de V2 a V4 que condicionan el modelo de V1** (se diseñan ahora aunque se construyan después):

| Historia futura | Qué exige desde V1 |
|---|---|
| HU-E01-03 Invitado | Que una cuenta pueda existir sin correo ni contraseña |
| HU-E08-02 Mazos propios | Que las sesiones y los estados no dependan de que el mazo sea del sistema |
| HU-E11-02, HU-E12-01 Planes y cobro | Que toda consulta de "¿puede estudiar esto?" pase ya por el motor de derechos |
| HU-E15-01 Pronunciación | Consentimiento por finalidad, cuotas y almacenamiento privado con plazo |
| Inglés | Todo `R-IDI`, verificado por las pruebas de `R-IDI-10` |

## 6. Lo que toda historia debe declarar

Además de sus criterios, cada historia de `docs/historias/` responde cinco preguntas. Si alguna no aplica, se escribe "no aplica"; no se omite.

1. **Derechos:** ¿qué capacidad consulta y qué ve quien no la tiene?
2. **Idioma:** ¿qué textos nuevos añade (claves) y depende del idioma de estudio?
3. **Guardado:** ¿qué pasa si se cae la red o se cierra la pestaña a la mitad?
4. **Analítica:** ¿qué eventos emite?
5. **Datos personales:** ¿guarda algo nuevo de la persona? ¿Se exporta y se borra con la cuenta?

## 7. Cobro: opciones abiertas

El motor de derechos (`R-DER-04`) admite las tres. En todas, un pago crea una *compra* y esta crea una o varias *concesiones*; lo que cambia es el alcance y la fecha de fin de la concesión.

| Opción | Cómo es | Efecto en el modelo de datos | A favor | En contra |
|---|---|---|---|---|
| **A. Suscripción** | Pro mensual o anual, con renovación automática | Concesión del plan Pro con fin que se renueva. **Añade** una tabla de suscripciones con su ciclo de estados (activa, en gracia, impaga, cancelada) y la recepción de avisos de la pasarela | Ingreso recurrente; es lo habitual | Es lo más complejo: cobros fallidos, cancelaciones, reembolsos parciales. Exige que el usuario tenga un medio de pago recurrente |
| **B. Pago único por nivel** | Se compra HSK 3, 4, 5 o 6 para siempre | Concesión perpetua de la capacidad `study.level.N`. Sin estados que mantener. La pronunciación, por su costo variable, se vendería aparte como paquete de usos (concesión de cuota sin renovación) | Simple y fácil de entender; encaja con "estudio para este examen" | Ingreso una sola vez por nivel; Pro deja de ser un plan y pasa a ser una suma de compras |
| **C. Pase por tiempo** | Pro por 3, 6 o 12 meses, pago único sin renovación | Concesión del plan Pro con fecha de fin fija. Sin suscripciones ni cobros fallidos. Al vencer se aplica `R-DER-08` | Casi tan simple como B; conserva "Pro" como plan con cuota de pronunciación; encaja con la temporada de examen; sirve con cualquier medio de pago | No renueva solo: hay que recordar al usuario que vence |

**Recomendación: empezar por C** y añadir A más adelante si los datos lo justifican (confianza media).

- Es la única que cumple tu definición de Pro (todo el contenido más pronunciación con cuota) sin construir la maquinaria de suscripciones.
- Añadir A después no cambia el modelo: es otro origen de concesión.
- B queda disponible como oferta puntual sin trabajo extra.

Antes de construir cualquiera de las tres, hay que confirmar qué pasarelas operan para un vendedor en Colombia; no lo he verificado.

## 8. Pendientes de este mapa

- **HU-E09-05** no tiene regla todavía: falta definir cómo se arma y se puntúa la prueba de aprendizaje.
- Los supuestos que bloqueaban V1a se cerraron el 22 nov 2026 (`04-decisiones.md`, sección 8). Queda abierto R-ESC-06, que bloquea V1b.
