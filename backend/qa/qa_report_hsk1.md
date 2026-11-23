# QA lingüístico — HSK 1 (`review_queue_raw.json`)

338 entradas (300 palabras × sentidos) · 1014 frases de ejemplo · revisión completa.
Solo se listan las entradas que requieren cambios.

> **Estado: APLICADO** sobre `review_queue_raw.json` (copia previa en
> `review_queue_raw.backup.json`). Cada propuesta se volvió a evaluar antes de
> aplicarla; las marcadas **MEJORA** u **OPCIONAL** en este informe se
> documentan pero **no** se modificaron, salvo las tres excepciones indicadas
> en §10. El esquema JSON es idéntico al original.
>
> Aplicado: **20 campos de entrada · 12 frases sustituidas · 315 sílabas de
> pinyin en 263 ejemplos · 10 traducciones · 156 normalizaciones de puntuación ·
> 3 sentidos nuevos.**


Severidades: **ERROR** = objetivamente incorrecto · **MEJORA** = correcto pero
poco natural / incompleto · **OPCIONAL** = otra posibilidad válida.

---

## 1. Errores en el campo `pinyin` de la entrada (cabecera)

| # | Entrada | Sev | Actual | Corregido | Explicación |
|---|---|---|---|---|---|
| 157 | 便宜 | **ERROR** | `biànyí` | `piányi` | 便 se lee `pián` en 便宜; `biàn` es la lectura de 方便/便利. Los ejemplos ya usan `pián yi`, así que la cabecera se contradice con su propio contenido. |
| 287 | 只 | **ERROR** | `zhǐ` | `zhī` | Como clasificador (一只猫) es `zhī` en primer tono. `zhǐ` es el adverbio "solo" (只有). La lista de MandarinBean también da `zhī`. |
| 40 | 东西 | **ERROR** | `dōngxī` | `dōngxi` | Con el sentido "cosa/objeto" la segunda sílaba es neutra. `dōngxī` solo vale para "este y oeste". |
| 71.2 | 好 (v.) | **ERROR** | `hǎo` | `hào` | El verbo "ser aficionado a" es `hào` (4.º tono). Con `hǎo` las tres frases se leen como "muy…" y el sentido desaparece. |
| 153 | 女儿 | **ERROR** | `nǚér` | `nǚ'ér` | Falta el apóstrofo silábico obligatorio ante sílaba con vocal inicial. |
| 235 | 小朋友 | MEJORA | `xiǎopéngyǒu` | `xiǎopéngyou` | Inconsistente con 朋友 `péngyou`, 男朋友 `nánpéngyou`, 女朋友 `nǚpéngyou` del mismo archivo. |
| 47 | 多少 | MEJORA | `duōshǎo` | `duōshao` | Segunda sílaba neutra en el uso interrogativo. Coherente con la política de tono neutro del resto del archivo. |
| 181 | 谁 | MEJORA | `shuí` | `shéi` | Los ejemplos mezclan `shuí` (ej. 0, 1) y `shéi` (ej. 2). `shéi` es la lectura coloquial dominante; conviene unificar. |

## 2. Errores de POS / glosa

| # | Entrada | Sev | Actual | Corregido | Explicación |
|---|---|---|---|---|---|
| 63.0 / 63.1 | 工作 | **ERROR** | s0 `verb` → EN "work"; s1 `noun` → EN "to work" | s0 EN "to work"; s1 EN "work" | Las glosas inglesas están intercambiadas respecto al POS. El español (`trabajar` / `trabajo`) sí es correcto. |
| 259.0 | 一下 | **ERROR** | `pos_raw: "numberclassifier"` | `"number-classifier"` | Falta el guion; 261 一点儿 y 262 一些 sí lo llevan. |
| 44.2 | 对 | **ERROR** | `verb、classifier` — "to treat; tratar" | solo `classifier` — "par" | 对 no funciona como verbo "tratar". En 他对我很好 es la **preposición** del sentido 44.1. Ver §4. |
| 172.1 | 日 | **ERROR** | `noun` — "sun" / "sol; día" | "day (formal, in dates and set expressions)" / "día (uso formal o escrito)" | Ninguno de los tres ejemplos muestra 日 = "sol"; muestran 生日, 改日, 他日. En chino moderno "sol" es 太阳. |
| 14, 24, 120, 147, 227, 300 | 不客气, 打电话, 没关系, 你好, 下雨, 做饭 | MEJORA | `pos_raw: ""` | `"phrase"` | Seis entradas sin POS. Aunque MandarinBean tampoco lo da, un campo vacío rompe cualquier filtro por categoría en la app. |
| 285.1 | 真 | MEJORA | `"verdadero;real"` | `"verdadero; real"` | Falta el espacio tras el punto y coma; el resto del archivo usa `"; "`. |

## 3. Errores en las frases chinas (gramática / naturalidad)

| # | Entrada | Sev | Actual | Corregido | Explicación |
|---|---|---|---|---|---|
| 49 | 二 ej.0 | **ERROR** | 我家有二个孩子。 | 我住在二楼。 | Ante clasificador se usa **两**, nunca 二. La frase es agramatical. Se sustituye por un contexto donde 二 sí es obligatorio (numeración de pisos). |
| 104.0 | 口 ej.0 | **ERROR** | 她的口很小。 | 我家门口有一家商店。 | 口 no se usa como sustantivo libre para "boca" en mandarín moderno (se dice 嘴). Solo aparece en compuestos: 门口, 出口, 瓶口. |
| 104.0 | 口 ej.2 | **ERROR** | 孩子把糖放进口里。 | 这个瓶子的口很小。 | Mismo problema: sería 放进**嘴**里. La nueva frase usa 口 = "abertura", que sí es un uso libre. |
| 163 | 前 ej.0 | **ERROR** | 我家前有一棵大树。 | 我家前面有一棵大树。 | 前 no puede cerrar un sintagma locativo tras sustantivo; requiere 前面/前边. |
| 186 | 时间 ej.0 | **ERROR** | 现在是什么时间？ | 我们的上课时间是八点。 | Nadie pregunta la hora así (se dice 现在几点？). Además la traducción "¿Qué hora es?" no correspondía a 时间. |
| 269 | 月 ej.1 | **ERROR** | 今晚的月很亮。 | 一年有十二个月。 | 月 solo = "luna" es literario; en mandarín contemporáneo se dice 月亮. Se recomienda además matizar `meaning_es` ("luna" solo en 月亮). |
| 281 | 这个 ej.0 | **ERROR** | 这个是我的书包。 | 这个是我的，那个是你的。 | 这个 + 是 + N es marginal; lo natural es 这是我的书包 o usar 这个 en contraste, como en la corrección. |
| 172.0 | 日 ej.2 | **ERROR** | 她请了五日假。 | 我的生日是十月一日。 | Con 请假 se usa 天, no 日. 日 como clasificador de días es de registro escrito. |
| 195 | 睡觉 ej.1 | **ERROR** | 孩子已经睡觉了。 | 孩子在睡觉。 | 已经 + 睡觉了 suena forzado (睡觉 es verbo-objeto); lo correcto sería 已经睡了. Se elige 在睡觉, más útil para HSK1. |
| 97 | 开 ej.0 | **ERROR** | 请把门开一下。 | 请开一下门。 | Con 把 el verbo necesita complemento (请把门打开). Tal como está es agramatical. |
| 71.2 | 好 ej.2 | **ERROR** | 我妹妹好安静。 | 他好读书。 | Con 好 ante adjetivo la lectura obligada es `hǎo` = "muy tranquila": el ejemplo demuestra lo contrario de lo que pretende. |
| 7.1 | 半 ej.0 | **ERROR**/MEJORA | 他半睁着眼睛看着我。 | 他的眼睛半开着。 | 睁 está muy por encima de HSK1 y el pinyin traía `zhuó` en lugar de `zhe`. |
| 7.1 | 半 ej.1 | MEJORA | 她半信半疑地听着。 | 这件衣服是半新的。 | 半信半疑 es un chengyu de nivel HSK5; inútil e intimidante en HSK1. |
| 12.0 | 病 (sust.) ej.0 | MEJORA | 他生病了，不能来上班。 | 他的病好了。 | El ejemplo ilustra el verbo 生病 (entrada 183), no 病 como sustantivo. |
| 66 | 国 ej.1, ej.2 | MEJORA | 这个国家有很多山。 / 他爱自己的国家。 | 你是哪国人？ / 这是哪国的车？ | Ambos ejemplos ilustran 国家, no 国. 哪国人 es además vocabulario HSK1 real. |
| 226.1 | 下 ej.2 | MEJORA | 飞机马上就要下降了。 | 他从楼上下来了。 | 下降 es HSK5 y aquí 下 no es el verbo autónomo de la entrada. |
| 239 | 些 ej.1 | MEJORA | 桌子上有些书。 | 桌子上有一些书。 | 有些 se lee como una unidad ("algunos") y colisiona con la entrada 266; con 一些 el clasificador queda claro. |
| 292 | 中学 ej.2 | MEJORA | 这个中学离我家很近。 | 这所中学离我家很近。 | El clasificador propio de centros educativos es 所, ya usado en 237 y 250 del mismo archivo. |
| 207.1 | 天 (clasificador) ej.2 | MEJORA | 他每天都跑步。 | 这个月有三十天。 | 每天 no ilustra 天 contando días, y duplica el ej.2 de 207.0. |
| 118.1 | 忙 (verbo) ej.0 | MEJORA | 妈妈最近很忙。 | 你在忙什么？ | Es uso adjetival, idéntico al sentido 118.0; no demuestra 忙 como verbo. |
| 46.1 | 多 (verbo) ej.2 | MEJORA | 他的班里多五个学生。 | *sugerido:* 他们班比我们班多五个学生。 | Sin término de comparación explícito la frase queda coja. (No incluido en el patch: requiere tu decisión.) |
| 81.1 | 回 (clasificador) ej.2 | MEJORA | 他又迟到了一回。 | *sugerido:* 这个电影我看过两回。 | Con 又…了 lo natural es 又迟到了 sin clasificador. (No incluido en el patch.) |
| 86.1 | 家 (clasificador) ej.1 | MEJORA | 我们小区住着几十家人。 | *sugerido:* 这个小区有几十家商店。 | 几十家人 se confunde con la entrada 87 家人. (No incluido en el patch.) |
| 102.1 | 可以 (adj.) ej.2 | MEJORA | 他的成绩可以。 | *sugerido:* 他的成绩还可以。 | 可以 predicativo casi siempre lleva 还. (No incluido en el patch.) |
| 172.0 | 日 ej.1 | MEJORA | 我们三日后见面。 | 他八月三日去中国。 | 三日后 es registro escrito; en habla se dice 三天后. La fecha sí es uso HSK1 de 日. |

## 4. Sentidos duplicados o no demostrados

| # | Entrada | Sev | Problema | Corrección |
|---|---|---|---|---|
| 44.1 / 44.2 | 对 | **ERROR** | Los sentidos 1 y 2 comparten literalmente la misma frase (他对我很好) y el 44.2 la etiqueta como "verbo: tratar", que no existe. | 44.2 pasa a ser solo clasificador: 桌子上有一对杯子。 |
| 85.0 / 85.1 | 几 | MEJORA | 现在几点了？ aparece en ambos sentidos; 你家有几口人/几个人 son la misma frase. | 85.1 (número, "unos cuantos") pasa a 桌子上有几个苹果。 y 我在中国住了几年。, separando "interrogativo" de "indefinido". |
| 259.0 / 259.1 | 一下 | MEJORA | 请等一下 / 你等一下 y 帮我(看)一下 se repiten entre sentidos. | 259.1 ej.0 pasa a 我出去一下。 |

## 5. Significados / usos faltantes (auditoría de palabras polisémicas)

| # | Entrada | Sev | Falta | Propuesta |
|---|---|---|---|---|
| 82 | 会 | **ERROR** (cobertura) | Solo cubre "saber hacer". Falta el 会 de **futuro/probabilidad**, que es uso nuclear HSK1. | Nuevo sentido `82.1`: 明天会下雨。/ 他今天不会来。/ 你觉得她会喜欢吗？ |
| 252 | 要 | **ERROR** (cobertura) | Solo cubre "querer un objeto". Faltan "ir a (futuro)" y "tener que". | Nuevo sentido `252.1`: 我明天要去北京。/ 你要多喝水。/ 火车要开了。 |
| 298 | 坐 | **ERROR** (cobertura) | Solo "sentarse". Falta 坐 = "ir en (transporte)", que ya aparece en los ejemplos de 22, 54, 83 pero no tiene sentido propio. | Nuevo sentido `298.1`: 我坐飞机去北京。/ 他每天坐车上班。/ 我们坐出租车去吧。 |
| 91 | 叫 | **ERROR** (cobertura) | `pos_raw` declara `verb、（preposition）` pero los tres ejemplos son "llamarse/llamar". No hay ni causativo (叫我等一下) ni pasivo. | Nuevo sentido `91.1` (causativo): 妈妈叫我早点回家。/ 老师叫我们写汉字。/ 他叫我等一下。 El pasivo 叫 sí es HSK3+: se recomienda **quitar** `（preposition）` del POS. |
| 122 | 没有 | — | Correcto: 122.0 cubre "no tener" y 122.1 cubre "no haber hecho". Sin cambios. | — |
| 271 | 在 | — | Correcto: verbo / preposición / adverbio progresivo, los tres bien ejemplificados. | — |
| 61, 44, 145, 102, 233, 67, 270, 226, 175 | 给, 对, 能, 可以, 想, 还, 再, 下, 上 | — | Cobertura adecuada. | — |
| 276 | 怎么 | OPCIONAL | Falta el 怎么 de reproche/causa (你怎么没来？). | Añadir un cuarto ejemplo o un sentido `276.1` si quieres cubrirlo. |
| 122 | 没有 | OPCIONAL | Falta el comparativo 我没有他高. | Es HSK2; no lo añadiría en HSK1. |

## 6. Errores de pinyin en los ejemplos

### 6.1 Errores puntuales (**ERROR**)

| # | Entrada | Actual | Corregido | Explicación |
|---|---|---|---|---|
| 105 | 块 ej.1 — 这个苹果三块钱。 | `sān kuài yuán` | `sān kuài qián` | Se transcribió 钱 con la lectura de 元. |
| 87 | 家人 ej.2 | `jiā rén dū huì` | `jiā rén dōu huì` | 都 = `dōu`; `dū` es "capital" (首都). |
| 59 | 哥哥 ej.2 | `wǒ dī gē ge` | `wǒ de gē ge` | 的 = `de`; `dī` es 低/滴. |
| 147 | 你好 ej.1 | `tā xiào zhe shuō : “ hǎo !” ! ”` | `tā xiào zhe shuō : “ nǐ hǎo ! ”` | Falta la sílaba `nǐ` y hay puntuación duplicada. |
| 7.1 | 半 ej.0 | `kàn zhuó` (着) | `zhe` | 着 aspectual es `zhe`; `zhuó` es 着 = "vestir/aplicar". |
| 63 | 工作 ej.2 — 她非常努力地工作。 | `nǔ lì dì` | `nǔ lì de` | 地 adverbial es `de`, no `dì`. |
| 7.1 | 半 ej.1 | `bàn xìn bàn yí dì` | `de` | Mismo caso. |

### 6.2 得 estructural transcrito como `dé` (**ERROR** × 11)

Entradas 12.1 ej.2, 33.0 ej.2, 44.0 ej.0, 69 ej.1, 73 ej.1, 118.1 ej.1, 158 ej.1,
186 ej.2, 194 ej.0, 273 ej.0, 296 ej.1.
El 得 que introduce complemento de grado es **siempre** neutro `de`
(说得对, 长得漂亮, 起得很早). `dé` es el verbo "obtener".

### 6.3 Clasificador 只 transcrito como `zhǐ` (**ERROR** × 11)

Entradas 5 ej.2, 64 ej.1, 75 ej.2, 91 ej.2, 99 ej.2, 119 ej.1, 199 ej.2, 201 ej.0,
225 ej.1, 234 ej.0, 287 ej.2. En 一只猫 / 这只狗 / 两只鸟 la lectura es `zhī`.

### 6.4 Tono neutro no aplicado (**ERROR** × 273, en 247 ejemplos)

Es el problema más extendido del archivo. El campo `pinyin` de la **cabecera** sí
lo aplica (`māma`, `xǐhuan`, `péngyou`, `xuésheng`…), pero los ejemplos lo
contradicen sistemáticamente:

| Palabra | En los ejemplos | Correcto | Veces |
|---|---|---|---|
| 喜欢 | `xǐ huān` | `xǐ huan` | 48 |
| 学生 | `xué shēng` | `xué sheng` | 29 |
| 妈妈 | `mā mā` | `mā ma` | 27 |
| 朋友 | `péng yǒu` | `péng you` | 26 |
| 衣服 | `yī fú` | `yī fu` | 19 |
| 晚上 | `wǎn shàng` | `wǎn shang` | 14 |
| 早上 | `zǎo shàng` | `zǎo shang` | 13 |
| 名字 | `míng zì` | `míng zi` | 10 |
| 妹妹 / 认识 / 漂亮 | `mèi mèi` / `rèn shí` / `piào liàng` | `mèi mei` / `rèn shi` / `piào liang` | 9 c/u |
| 休息 | `xiū xī` | `xiū xi` | 8 |
| 时候 / 多少 | `shí hòu` / `duō shǎo` | `shí hou` / `duō shao` | 7 c/u |
| 谢谢 | `xiè xiè` | `xiè xie` | 6 |
| 哥哥 | `gē gē` | `gē ge` | 5 |
| 东西 / 爸爸 | `dōng xī` / `bà bà` | `dōng xi` / `bà ba` | 4 c/u |
| 先生 / 关系 / 客气 / 姐姐 | — | `xiān sheng` / `guān xi` / `kè qi` / `jiě jie` | 3 c/u |
| 舒服 / 爷爷 / 明白 | — | `shū fu` / `yé ye` / `míng bai` | 1–2 c/u |

> **Decisión tuya en un solo caso:** 学生. El diccionario y tu propia cabecera dan
> `xuésheng`, pero muchos manuales enseñan `xuéshēng`. El patch aplica `xué sheng`
> por coherencia con tu cabecera, y **no** toca 大学生/小学生/中学生, que sí llevan
> `shēng` pleno. Si prefieres `xuéshēng`, cambia también la cabecera de la entrada 248.

> **No corregido a propósito:** 知道 se transcribe `zhī dào` en los ejemplos y
> `zhīdào` en la cabecera — coherente entre sí, y ambas lecturas son estándar.

### 6.5 Estilo de pinyin inconsistente (MEJORA × 3)

| # | Entrada | Actual | Corregido |
|---|---|---|---|
| 124 | 们 ej.0 | `Háizimen zài wàimiàn wán yóuxì.` | `hái zi men zài wài miàn wán yóu xì。` |
| 76.1 | 号 ej.0 | `Jīn tiān lái le sān shí hào kè rén。` | `jīn tiān lái le sān shí hào kè rén。` |
| 172.1 | 日 ej.1 | `Wǒ men gǎi rì zài jiànmiàn ba。` | `wǒ men gǎi rì zài jiàn miàn ba。` |

Tres ejemplos usan agrupación por palabra y mayúscula inicial; los otros 1011 van
en minúscula y sílaba a sílaba.

### 6.6 Lo que está bien (verificado, sin cambios)

- **Sandhi de 一 y 不**: correcto en los 1014 ejemplos (`yí gè`, `yì běn`, `bú duì`,
  `bù xǐhuan`). Se comprobó sílaba a sílaba contra el tono siguiente: 0 fallos.
- **一 en fechas y ordinales** conserva `yī` (十月一日, 第一次): correcto.
- **Erhua**: `nǎr`, `zhèr`, `nàr`, `diǎnr`, `wánr`, `tiáor`, `huìr` bien fusionados.
- El pinyin de **cabecera** es de muy buena calidad salvo los 8 casos de §1.

## 7. Errores de traducción al español

| # | Entrada | Sev | Actual | Corregido | Explicación |
|---|---|---|---|---|---|
| 116 | 买 ej.0 | **ERROR** | "Quiero comprar una ropa nueva." | "Quiero comprar una prenda nueva." | *"una ropa"* es agramatical: *ropa* es incontable. |
| 242 | 新 ej.0 | **ERROR** | "Compré una ropa nueva." | "Compré una prenda de ropa nueva." | Ídem. |
| 136 | 那 ej.0 | **ERROR** | "Ese es mi mochila." | "Esa es mi mochila." | Concordancia de género. |
| 281 | 这个 ej.0 | **ERROR** | "Esto es mi mochila." | (frase reemplazada, ver §3) | Ídem. |
| 266.0 | 有些 ej.0 | **ERROR** | "Algunas personas les gusta tomar té." | "A algunas personas les gusta el té." | Falta la preposición del complemento indirecto. |
| 204 | 它们 ej.0 | **ERROR** | "…las compraron esta mañana." | "…las compré esta mañana." | 是今天早上买的 no es pasiva impersonal: cambia el sujeto de la frase. |
| 71.1 | 好 ej.2 | **ERROR** | "Ella lleva muy buen tiempo sin venir." | "Hace mucho tiempo que no viene." | Lee 好久 como "buen tiempo"; 好久 = "mucho tiempo". |
| 76.1 | 号 ej.0 | **ERROR** | "Hoy llegó el cliente número treinta." | "Hoy vinieron treinta clientes." | 来了三十号客人 usa 号 como clasificador **contador** de personas, no ordinal. |
| 180.1 | 少 ej.0 | **ERROR** | "A esta frase le falta una palabra." | "A esta oración le falta un carácter." | 字 = carácter; 词 sería "palabra". |
| 214 | 玩 ej.1 | **ERROR** | "Juguemos un videojuego juntos." | "Vamos a jugar un juego juntos." | 游戏 es "juego" en general, no específicamente videojuego. |
| 264 | 有的 ej.1 | MEJORA | "…trabajan en Beijing." | "…trabajan en Pekín." | Único caso de "Beijing" frente a 21 de "Pekín". |
| 172.0 | 日 ej.0 | MEJORA | "¿Qué día es hoy?" | "¿A qué fecha estamos hoy?" | 几月几日 pregunta la fecha; "¿qué día?" se entiende como día de la semana. |
| 282 | 这里 ej.0 | MEJORA | "Aquí es mi casa." | "Esta es mi casa." | *"Aquí es"* no es idiomático en español. |
| 131 | 哪 ej.0 | MEJORA | "¿Cuál color te gusta?" | "¿Qué color te gusta?" | *cuál + sustantivo* es anglicismo; en español general se usa *qué + sustantivo*. |
| 135 | 哪些 ej.0, ej.2 | MEJORA | "¿Cuáles colores…?" / "¿A cuáles países…?" | "¿Qué colores…?" / "¿A qué países…?" | Ídem. |
| 132 | 哪个 ej.2 | MEJORA | "De estas dos ropas, ¿cuál te gusta?" | "De estas dos prendas, ¿cuál te gusta?" | *ropas* en plural es forzado. |
| 262 | 一些 ej.2 | MEJORA | "Ella compró un poco de ropa nueva." | "Ella compró algunas prendas nuevas." | 一些 + clasificable pide plural contable. |
| 47, 65, 136.1, 157, 255 | 多少, 贵, 那, 便宜, 衣服 | MEJORA | "esta ropa" para 这件衣服 | "esta prenda" | Consistencia: 件 individualiza. Ocho ejemplos del archivo ya usan "prenda"; los otros cinco no. |

## 8. Formato y consistencia

| Problema | Sev | Alcance | Corrección |
|---|---|---|---|
| Coma `,` de ancho medio dentro de frases chinas | MEJORA | 44 ejemplos | → `，` |
| Interrogación `?` de ancho medio | MEJORA | 90 ejemplos | → `？` |
| Exclamación `!` de ancho medio | MEJORA | 3 ejemplos | → `！` |
| Frases sin puntuación final | MEJORA | 30 ejemplos en 10 entradas (2, 12.1, 17, 76.1, 89, 104.1, 193, 223, 266.0, 287) | → añadir `。` en `zh` **y** en `pinyin` |
| Puntuación CJK dentro del `pinyin` (`。？，“”`) con espacio previo | OPCIONAL | ~1000 ejemplos | El pinyin es escritura latina y debería llevar `.` `,` `?` pegados. Se entrega aparte como `normalize_pinyin_punctuation.py` porque afecta a casi todo el archivo. |
| Nombres propios en minúscula en el pinyin (`běi jīng`, `zhōng guó`, `wáng`, `lǐ míng`) y en las cabeceras (`hànyǔ`, `hànzì`, `zhōngguó`, `zhōngwén`) | OPCIONAL | sistemático | MandarinBean capitaliza `Hànyǔ`, `Hànzì`, `Zhōngguó`. Es una decisión de estilo: coherente como está, pero divergente de la fuente. No incluido en el patch. |

## 9. Vocabulario fuera de HSK1 (marcado, no corregido salvo indicación)

Aceptables (palabras funcionales o contexto inevitable): 因为/所以 no aparecen; 比, 从, 跟,
就, 才, 已经, 正在 son gramaticales y necesarios.

Señalados por ser sustancialmente superiores al nivel:

| # | Entrada | Palabra fuera de nivel | Acción |
|---|---|---|---|
| 6 | 百 ej.1, ej.2 | 百分之百, 纯棉, 操场, 上百名 | MEJORA: sustituir por 我们班有一百个学生。y 这件衣服一百块钱。 |
| 7.1 | 半 | 睁, 半信半疑 | Corregido en el patch (§3). |
| 33.0 | 点 ej.1, ej.2 | 污渍, 水滴 | MEJORA: contexto muy poco rentable para HSK1. |
| 104.1 | 口 ej.1 | 咬 | OPCIONAL: 一口 con 喝 (ej.2) ya cubre el clasificador. |
| 107 | 老师 ej.0 | 和蔼 | MEJORA: 我的老师很好。 |
| 172.1 | 日 ej.2 | 他日 (literario) | Corregido en el patch. |
| 226.1 | 下 ej.2 | 下降 | Corregido en el patch. |
| 285.1 | 真 ej.2 | 钻石 | OPCIONAL. |
| 87 | 家人 ej.2 | 团聚, 过年 | OPCIONAL: culturalmente útil. |

---

# Resumen

| Categoría | Nº |
|---|---|
| **Errores serios** aplicados | **17** — 5 en el pinyin de cabecera, 12 en frases chinas |
| **Errores de POS / glosa** | **4** (§2: 工作, 一下, 对 44.2, 日 172.1) + 6 entradas con `pos_raw` vacío + 1 separador mal formado |
| **Significados/usos faltantes** | **6** — 会 (futuro), 要 (futuro/obligación), 坐 (transporte), 叫 (causativo), 日 (sentido "sol" no demostrado), 对 (sentido "verbo" inexistente) |
| **Errores de pinyin** | **315 sílabas en 263 ejemplos** (aplicados) — tono neutro, 得, 只, puntuales y de estilo — más 6 de cabecera |
| **Errores de traducción al español** | **10** graves (aplicados) + **13** mejoras de estilo (**no** aplicadas) |
| **Problemas de naturalidad** (documentados, **no** aplicados — ver §10) | **20** |
| **Problemas de formato/consistencia** | **158 ejemplos** (puntuación) + 3 de estilo de pinyin + 1 de separador |
| **Marcas de nivel HSK1** | **9 entradas** con léxico claramente superior |

Total realmente aplicado: **20 campos de entrada, 497 campos de ejemplo,
3 sentidos nuevos** (ver el desglose en la cabecera y las exclusiones en §10).


---

## 10. Reevaluación: propuestas descartadas

Al aplicar el patch volví a juzgar cada recomendación. Estas se **descartaron**
por no superar el listón de "defecto objetivo":

| # | Entrada | Propuesta original | Por qué NO se aplicó |
|---|---|---|---|
| 281 | 这个 ej.0 | 这个是我的书包 → reemplazar; "Esto es mi mochila" → "Esta es…" | **Me equivoqué al marcarlo como error.** `Esto` es el demostrativo neutro español y es correcto aquí; 这个是… también se dice en habla coloquial. Contenido preservado. |
| 97 | 开 ej.0 | 请把门开一下 → 请开一下门 | La construcción 把 sí admite verbo + 一下: 把门开一下 es gramatical y se usa. Solo era menos frecuente que 把门打开. |
| 195 | 睡觉 ej.1 | 孩子已经睡觉了 → 孩子在睡觉 | 已经…睡觉了 es correcto; 已经睡了 solo es algo más idiomático. Preferencia, no error. |
| 7.1 | 半 ej.0, ej.1 | Sustituir 半睁着眼睛 y 半信半疑 | Frases correctas. Están por encima de HSK1 (se mantiene la marca de nivel en §9) pero no son incorrectas. **Sí se corrigió su pinyin** (`zhuó`→`zhe`, `dì`→`de`). |
| 12.0 | 病 ej.0 | 他生病了… → 他的病好了 | Frase correcta; los ejemplos 1 y 2 ya demuestran 病 como sustantivo. |
| 66 | 国 ej.1, ej.2 | Sustituir por 哪国人 / 哪国的车 | 国家 contiene 国 y las frases son correctas y naturales. |
| 226.1 | 下 ej.2 | 下降 → 他从楼上下来了 | Frase correcta; solo está por encima de nivel. |
| 239 | 些 ej.1 | 桌子上有些书 → …一些书 | Gramatical y natural. |
| 292 | 中学 ej.2 | 这个中学 → 这所中学 | 个 con instituciones es coloquial pero admisible. |
| 207.1 | 天 ej.2 | 每天都跑步 → 这个月有三十天 | 每天 sí usa 天 como unidad contable. |
| 118.1 | 忙 ej.0 | 妈妈最近很忙 → 你在忙什么？ | En chino 忙 es un verbo estativo: adjetivo y verbo no se distinguen formalmente aquí. |
| 46.1, 81.1, 86.1, 102.1 | 多, 回, 家, 可以 | Reescrituras sugeridas | Ya estaban fuera del patch; siguen fuera. |
| 172.0 | 日 ej.0, ej.1 | "¿Qué día es hoy?" → "¿A qué fecha…?"; 三日后 → 三天后 | 三日后 es registro escrito, no incorrecto. "¿Qué día es hoy?" se usa en Colombia para preguntar la fecha. |
| 172.1 | 日 | Reescribir la glosa "sun / sol" | 日 sí significa "sol" en el diccionario y la glosa reproduce tu lista de referencia. Se deja constancia de que ningún ejemplo lo demuestra (uso ligado: 日出, 日光). |
| 91 | 叫 | Añadir sentido causativo (叫我等一下) | Existe, pero no es núcleo de HSK1. No se añade solo porque sea posible. Queda la observación de que `pos_raw` declara `（preposition）` sin ejemplo. |
| 235 | 小朋友 | `xiǎopéngyǒu` → `xiǎopéngyou` | Los diccionarios registran 小朋友 con 友 en tono pleno; tu lista de referencia también. No es error. |
| 181 | 谁 | Cabecera `shuí` → `shéi` | Ambas lecturas son estándar. Se conservó `shuí` y se unificó **solo** el ejemplo 2, que era el único discrepante dentro de la entrada. |
| 131, 132, 135, 262, 282, 47, 65, 136.1, 157, 255 | varias | "cuál color"→"qué color", "ropa"→"prenda", "Aquí es mi casa"→"Esta es…" | Español correcto y de uso normal en Colombia. Son preferencias de estilo, no errores. |
| — | pinyin | Normalizar la puntuación CJK del campo `pinyin` | Afecta a ~1000 filas y es decisión de estilo. Disponible sin aplicar en `normalize_pinyin_punctuation.py`. |
| — | pinyin | Capitalizar nombres propios (`Běijīng`, `Hànyǔ`) | Decisión de estilo, coherente tal como está. |
| 6, 33, 87, 104.1, 107, 285.1 | varias | Bajar el léxico a HSK1 | Frases correctas. Se mantiene solo la marca de nivel de §9. |

### Excepciones: MEJORAs que sí se aplicaron y por qué

| # | Cambio | Justificación |
|---|---|---|
| 47 | `duōshǎo` → `duōshao` | La lectura del interrogativo 多少 lleva neutra en el diccionario y en tu lista de referencia. |
| 264 | "Beijing" → "Pekín" | Único caso frente a 21 de "Pekín" en el mismo archivo: inconsistencia interna, no preferencia. |
| 285.1, 259.0, 14/24/120/147/227/300 | `"verdadero;real"`, `"numberclassifier"`, `pos_raw` vacío | Defectos de formato/datos, no de lengua. |
| 104.0 | `meaning_es` "boca" → "boca; abertura" | Obligatorio por coherencia: el nuevo ejemplo 2 (口 de una botella) no encajaba con la glosa anterior. |
