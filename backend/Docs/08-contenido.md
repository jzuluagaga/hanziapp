# 08 · Contenido

**Para qué sirve:** es el manual de operación del editor: de dónde sale cada dato, qué licencia tiene, qué pasos sigue una palabra hasta publicarse y qué debe cumplir un nivel para abrirse. Las reglas están en `03-reglas-de-negocio.md` (`R-CON`); aquí está el procedimiento.

**Tope de extensión:** 170 líneas. **Estado:** primera versión (15 nov 2026).

---

## 1. Fuentes y licencias

| Dato | Fuente | Uso en el producto | Obligación | Estado |
|---|---|---|---|---|
| Lista de palabras, hanzi, pinyin, nivel | Sílabo oficial del examen HSK (noviembre de 2025) | Se muestra siempre (`R-CON-01`) | Citar la fuente en créditos | Cotejar cada nivel contra el documento oficial antes de publicarlo |
| Glosa en inglés por palabra | Listas de un tercero (Mandarin Bean) | **Solo interno**, como ancla de significado al generar (`R-CON-02`) | No mostrar ni redistribuir | Términos de uso **sin verificar** |
| Entradas de diccionario | CC-CEDICT | Solo interno, como contraste al revisar | Si algún día se muestra: atribución y misma licencia para lo derivado | Licencia Creative Commons Atribución-CompartirIgual |
| Lista de escritura (书写字) | Sílabo oficial, transcrita en `content/pipeline/data/writing_list.json` | Qué caracteres entran en escritura y desde qué nivel (`R-ESC-10`) | Citar la fuente en créditos | Cargada con `load_writing_list`; 700 caracteres (50, 50 y 150 por nivel de HSK 3 a 6), cotejada con el sílabo |
| Datos de trazos | Make Me a Hanzi, a través de Hanzi Writer | Animación y práctica de escritura | Aviso de la Arphic Public License y de la licencia MIT de Hanzi Writer en créditos | Verificado en `EVALUACION-PRODUCTO.md`, sección 4.5 |
| Significados en español, oraciones y traducciones | Generados con IA y revisados por una persona | Contenido propio | Revisión humana antes de publicar (`R-CON-07`) | Condiciones de uso comercial del proveedor **sin verificar** |
| Audio | Síntesis de voz | Audio de palabras y ejemplos | La que fije el proveedor | Condiciones de uso comercial **sin verificar** |

**Antes de abrir al público (V2)** hay que leer y anotar aquí las tres condiciones sin verificar. Mientras tanto no se cobra por el contenido.

**Página de créditos** (`R-CON-15`): nombra el sílabo, Make Me a Hanzi con su licencia Arphic, Hanzi Writer y la síntesis de voz. No nombra las fuentes de uso interno, porque nada de ellas se muestra.

## 2. Recorrido de una palabra

Cada paso es un comando que se puede repetir sin duplicar nada: una segunda ejecución no crea filas nuevas.

| Paso | Qué hace | Deja | Regla |
|---|---|---|---|
| 1. `load_syllabus` | Carga las palabras de un nivel con sus datos del sílabo y su orden | Palabras en estado "sin contenido", visibles en el diccionario como "en revisión" | R-CON-01, R-CON-03 |
| 2. `check_syllabus` | Compara lo cargado con el documento oficial: conteo por nivel, hanzi y pinyin | Informe de diferencias; debe quedar en cero | R-CON-01 |
| 3. `load_characters` y `load_writing_list` | Enlaza los datos de trazos de cada carácter y marca los de la lista de escritura con su nivel | Caracteres; lista de los que no tienen trazos | R-CON-12, R-ESC-10 |
| 4. `generate_drafts` | Genera acepciones, tres ejemplos por acepción y sus traducciones al idioma indicado | Un borrador de base y uno de contenido por idioma | R-CON-04, R-CON-07 |
| 5. `validate_drafts` | Ejecuta las validaciones de la sección 3 | Resultado por borrador | R-CON-06 |
| 6. `synthesize_audio` | Genera el audio de la palabra y de cada ejemplo que no lo tenga | Archivos de audio enlazados al borrador | R-CON-13 |
| 7. Revisión en el panel | El editor lee, corrige y marca cada palabra | Borrador revisado; cada edición revalida | R-CON-06 |
| 8. Publicar | Convierte el borrador en la versión publicada | Palabra visible y estudiable | R-CON-05 |
| 9. `check_level_ready` | Comprueba la lista de la sección 5 | Informe del nivel | R-CON-16 |

El pinyin de la palabra viene del sílabo y no se recalcula a partir del hanzi. El pinyin de los ejemplos se genera con las reglas de cambio de tono ya resueltas en la tubería y lo confirma la revisión.

## 3. Validaciones automáticas

Un borrador con alguna validación fallida no se puede publicar (`R-CON-06`). Cada una tiene un código, que es lo que ve el editor.

| Código | Comprueba | Capa |
|---|---|---|
| `word_in_example` | La palabra aparece, literal, en cada uno de sus ejemplos | Base |
| `example_hanzi_only` | El ejemplo solo tiene caracteres chinos y puntuación china | Base |
| `example_pinyin_matches` | El pinyin del ejemplo corresponde, sílaba a sílaba, a sus caracteres | Base |
| `example_length` | El ejemplo no supera la longitud máxima fijada para el nivel | Base |
| `example_level` | Las demás palabras del ejemplo pertenecen al mismo nivel o a uno inferior, con la tolerancia fijada | Base |
| `examples_distinct` | Los ejemplos de una palabra no repiten la misma plantilla | Base |
| `sense_count` | Hay al menos una acepción y cada una tiene categoría gramatical | Base |
| `translation_language` | Significados y traducciones están en el idioma declarado, sin restos de otro | Idioma |
| `translation_complete` | Cada acepción y cada ejemplo tienen su texto en ese idioma | Idioma |
| `not_third_party_copy` | El significado no es copia literal de una glosa de terceros | Idioma |
| `audio_present` | La palabra y sus ejemplos tienen audio | Base |

Las tolerancias de `example_length` y `example_level` son parámetros por nivel y se fijan al preparar cada nivel.

## 4. Revisión humana

Lo que el editor comprueba en cada palabra, además de lo automático:

1. El significado en español es el que un estudiante de ese nivel necesita, no una definición de diccionario.
2. En clasificadores, partículas y afijos, el significado explica el uso y no copia una descripción gramatical.
3. Cada ejemplo es natural y usa la palabra con la acepción que ilustra.
4. La traducción dice lo mismo que el ejemplo, en español natural.
5. Los tonos del pinyin son correctos, incluidos los cambios de tono y el tono neutro.
6. El audio pronuncia lo que está escrito.

**Gravedad de un error**, para medir y para priorizar reportes:

| Gravedad | Qué es | Ejemplo |
|---|---|---|
| Grave | Enseña algo falso | Significado equivocado, tono incorrecto, oración agramatical |
| Leve | Correcto pero mejorable | Traducción rígida, ejemplo poco natural |

## 5. Cuándo un nivel está listo

Un nivel se puede mostrar incompleto (`R-CON-16`), pero **se anuncia como disponible** solo cuando cumple todo esto:

| Condición | Cómo se comprueba |
|---|---|
| El sílabo cargado coincide con el oficial | `check_syllabus` sin diferencias |
| El 100 % de las palabras está publicado en español | `check_level_ready` |
| Todas las versiones publicadas tienen revisor y validaciones aprobadas | Consulta de `Q-23` con cero filas |
| Toda palabra tiene audio, y todo carácter con datos de trazos está enlazado | `check_level_ready` |
| El revisor domina el nivel | HSK 1 y 2: el fundador. HSK 3 en adelante: otra persona (`D-08`) |
| En HSK 3 en adelante, una muestra pasó revisión externa | 100 palabras al azar revisadas por un hablante nativo o profesor; 2 % o menos con error grave (experimento 5 de `EVALUACION-PRODUCTO.md`) |

## 6. Corregir y retirar

| Situación | Qué se hace | Efecto en el estudiante |
|---|---|---|
| Error en una palabra publicada | Se crea un borrador a partir de la versión publicada, se corrige, revalida y publica | Ve la corrección de una vez; conserva su progreso (`R-CON-05`, `R-CON-11`) |
| Error grave que no puede esperar | Se retira la versión publicada | La palabra pasa a "en revisión" y sale de las colas hasta republicarse |
| El hanzi o el pinyin del sílabo estaba mal cargado | Se corrige el dato; el identificador no cambia | Conserva su progreso (`R-CON-03`) |
| Una palabra cambia de nivel o sale del sílabo | Se actualiza el nivel o se marca como retirada | `R-CON-11` (b) y (c) |
| Se cambia de voz | Se genera el audio nuevo junto al anterior y se cambia la voz vigente | El audio anterior sigue disponible hasta el cambio (`R-IDI-08`) |

Todo cambio queda en el registro de auditoría con autor, fecha y motivo (`R-DAT-10`).

## 7. Mazos del sistema

Hoy cada nivel se divide en tramos de `system_deck_size` palabras en el orden del sílabo (`R-MAZ-02`, `D-43`). **Decidido (D-49): pasarán a mazos por tema** cuando la asignación esté construida y revisada. La lista y las reglas viven como dato en `content/pipeline/data/themes.json`; los nombres se muestran por clave (`R-IDI-09`).

**11 temas y 46 subtemas**, en orden pedagógico: Personas y relaciones · Comunicación · Números y tiempo · Vida diaria · Lugares y movimiento · Estudio y trabajo · Cuerpo y naturaleza · Sociedad y cultura · Acciones y procesos · Cómo es algo · Gramática. Los subtemas de cada uno están en el archivo de datos.

**Clasificación** (una sola vez, en el subtema; propuesta generada y revisada por el editor):

1. Un solo subtema por palabra: el de su acepción principal (D-14).
2. Las palabras funcionales van a Gramática; un adverbio solo sale de ahí si es una fórmula social fija.
3. Los sustantivos de tiempo van a Números y tiempo.
4. Gana el dominio más específico (饭店 → Comida y bebida; 司机 → Trabajo y oficios).
5. Un verbo va a Acciones y procesos solo si no pertenece a un dominio (穿 → Ropa; 聊 → Hablar y conversar).

**Armado por nivel**, con objetivo T = `system_deck_size` del nivel y banda [0,5 T; 1,5 T]:

| Caso | Qué se hace | Nombre del mazo |
|---|---|---|
| El tema entero cabe en 1,5 T y tiene 8 palabras o más | Un mazo con todo el tema | El del tema |
| El tema supera 1,5 T | Se divide por subtemas: primero se parten los mayores de 1,5 T y después cada grupo menor de 0,5 T se junta con el vecino que dé el grupo más pequeño | El de sus subtemas ("Subtema A · Subtema B") |
| Al dividir, un subtema queda repartido entre mazos o un mazo junta tres o más subtemas | Igual que arriba | Todos los mazos del tema se llaman "Tema · Parte n" |
| Un tema tiene menos de 8 palabras en el nivel | Se junta con el tema siguiente en el orden (o el anterior, si es el último) | "Tema A · Tema B" |
| El nivel no tiene todos sus temas aprobados | Tramos de `system_deck_size` en el orden del sílabo | "Mazo n" |

Ningún mazo queda con menos de 8 palabras. El mazo guarda las claves que contiene y la interfaz une sus traducciones: no hay claves nuevas por fusión. Dentro de cada mazo, las palabras van en el orden del sílabo. Se arma con `build_system_decks`; con los temas aprobados de HSK 1 y 2 salen 14 y 11 mazos. Rehacer los mazos no toca el progreso, que pertenece a la palabra, pero cambia los mazos que el estudiante conocía: por eso la asignación se cierra antes de publicar un nivel.

## 8. Añadir un idioma de estudio

Es el procedimiento que `R-IDI-10` promete que basta:

1. `generate_drafts --language en` sobre las palabras cuya base ya está publicada. No se generan acepciones ni ejemplos nuevos: solo significados y traducciones.
2. `validate_drafts`, revisión y publicación, igual que en español.
3. Traducir las claves de interfaz nuevas y la política de datos.
4. Encender los interruptores del idioma.

Si algún paso exige tocar código o esquema, es un defecto, y `test_add_language_without_migration` debe haberlo detectado antes.

## 9. Esfuerzo

| Dato | Valor | Origen |
|---|---|---|
| HSK 1 ya cargado | 300 palabras, 341 acepciones, 1.023 ejemplos | Estado actual del proyecto |
| Palabras acumuladas por nivel | 300, 500, 1.000, 2.000, 3.600, 5.400 | Sílabo de 2025 |
| Revisión por palabra | 2 a 3 minutos con sus ejemplos | Estimación mía, sin medir |
| HSK 2 (200 palabras nuevas) | 7 a 10 horas de revisión | Cálculo sobre la estimación anterior |
| HSK 1 a 6 completos | 180 a 270 horas por idioma | Ídem |

Medir el tiempo real de revisión de HSK 2 y sustituir la estimación.

## 10. Pendientes

- Verificar las tres condiciones de uso marcadas en la sección 1.
- Decidir el orden de estudio dentro de un nivel (sección 7).
- Encontrar revisor para HSK 3 antes de generar ese nivel.
- Confirmar las tolerancias propuestas para HSK 1 y 2 de `example_length` y `example_level` (`03-reglas-de-negocio.md`, sección 11). Se midieron sobre el contenido HSK 1 ya revisado: mediana de 7 caracteres por ejemplo y 84 % de ejemplos con una palabra o menos por encima del nivel.
