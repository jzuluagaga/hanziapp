"""
Pinyin determinista de los ejemplos (08-contenido.md §2: "El pinyin de los
ejemplos se genera con las reglas de cambio de tono ya resueltas en la
tubería y lo confirma la revisión").

El modelo de lenguaje nunca escribe pinyin. Este módulo lo calcula así:

1. Segmenta la oración en palabras con su función gramatical (jieba).
2. Lee cada palabra con pypinyin, ampliado con CC-CEDICT (fuente de uso
   interno, 08-contenido.md §1), que sí marca el tono neutro de palabras
   como 爸爸 bàba, 衣服 yīfu, 晚上 wǎnshang.
3. Aplica las lecturas de la lista de excepciones
   (data/pinyin_overrides.json), que es dato y puede ampliarse.
4. Resuelve las partículas por su función: 的/地/得 → de, 着 → zhe, 了 → le,
   y el clasificador 只 → zhī.
5. Aplica los cambios de tono de 一 y 不 sobre la oración ya leída.
6. Fusiona el erhua (哪儿 → nǎr) salvo cuando 儿 es una sílaba plena (女儿).

Formato de salida (canónico, el que valida `example_pinyin_matches`):
una sílaba por carácter, separadas por un espacio; el erhua va unido a su
sílaba; la puntuación china se escribe con su equivalente occidental, pegada
a la sílaba anterior. Ejemplo: "你去哪儿？" → "nǐ qù nǎr?".
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from pypinyin import Style, pinyin as _pypinyin
from pypinyin.contrib.tone_convert import to_tone, to_tone3

_DATA_DIR = Path(__file__).resolve().parent / "data"

# Puntuación china permitida en un ejemplo y su forma en pinyin.
CHINESE_PUNCTUATION = {
    "，": ",", "。": ".", "！": "!", "？": "?", "、": ",", "；": ";",
    "：": ":", "“": "\"", "”": "\"", "‘": "'", "’": "'", "（": "(",
    "）": ")", "《": "\"", "》": "\"", "…": "...", "—": "-", "·": "·",
}
_OPENING = {"“", "‘", "（", "《"}

# Caracteres en los que 儿 es una sílaba plena y no erhua.
_FULL_ER_WORDS = {"女儿", "儿子", "儿童", "婴儿", "孤儿", "儿科", "幼儿", "儿女", "健儿", "胎儿", "男儿"}

# Contexto que convierte 只 en clasificador (zhī) en vez de adverbio (zhǐ).
_ZHI_CLASSIFIER_PREV = set("这那哪几每一二两三四五六七八九十半")

# Contextos en los que 一 conserva el primer tono.
_DIGITS = set("零〇一二三四五六七八九十百千万亿两")
_YI_KEEP_NEXT = set("月号日")          # fechas: 一月, 一号, 一日
_YI_KEEP_WORDS = {"统一", "唯一", "万一", "星期一", "第一", "初一", "十一"}

_PARTICLE_BY_POS = {"uj": "de5", "uv": "de5", "ud": "de5", "uz": "zhe5", "ul": "le5"}


def is_chinese_char(ch: str) -> bool:
    return "一" <= ch <= "鿿" or "㐀" <= ch <= "䶿" or ch == "〇"  # 〇 líng: 二〇〇八年


@lru_cache(maxsize=1)
def _overrides() -> dict[str, list[str]]:
    with open(_DATA_DIR / "pinyin_overrides.json", encoding="utf-8") as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith("_")}


_ready = False


def _setup() -> None:
    """Carga CC-CEDICT en pypinyin y silencia jieba. Idempotente."""
    global _ready
    if _ready:
        return
    import jieba
    from pypinyin_dict.phrase_pinyin_data import cc_cedict

    jieba.setLogLevel(60)
    cc_cedict.load()
    for word in _overrides():
        jieba.add_word(word)
    _ready = True


@dataclass
class _Syl:
    char: str
    numbered: str          # p. ej. "ma1", "ma5"
    word: str              # palabra (segmento) a la que pertenece
    index_in_word: int
    fixed: object = None   # palabra del sílabo que fija la lectura (para el 一 de 一流)


def _numbered(text: str) -> list[str]:
    return [x[0] for x in _pypinyin(text, style=Style.TONE3, neutral_tone_with_five=True)]


def _base_tone(char: str) -> int:
    """Tono de la lectura aislada de un carácter (para el sandhi de 一/不)."""
    syl = _numbered(char)[0]
    m = re.search(r"([1-5])$", syl)
    return int(m.group(1)) if m else 5


def _tone(numbered: str) -> int:
    m = re.search(r"([1-5])$", numbered)
    return int(m.group(1)) if m else 5


def _with_tone(numbered: str, tone: int) -> str:
    return re.sub(r"[1-5]$", "", numbered) + str(tone)


# 着 se lee zhe salvo en estas palabras.
_ZHAO_ZHUO = {"着急": ["zhao2", "ji2"], "睡着": ["shui4", "zhao2"], "着凉": ["zhao2", "liang2"],
              "着火": ["zhao2", "huo3"], "着迷": ["zhao2", "mi2"], "衣着": ["yi1", "zhuo2"],
              "着想": ["zhuo2", "xiang3"], "着手": ["zhuo2", "shou3"]}
# 得 se lee dé solo en estas palabras; en lo demás, tras un verbo es partícula.
_DE2_WORDS = {"得到", "获得", "取得", "得分", "得意", "难得", "不得不", "只得", "得病", "值得", "记得", "觉得", "懂得", "晓得"}

# 过 conserva guò en estas palabras aunque vaya al final (no es la partícula guo).
_GUO4_WORDS = {"难过", "经过", "通过", "超过", "路过", "度过", "不过", "错过", "放过", "改过"}

# 为 se lee wéi ("como, ser") pegado a estos verbos (选为, 视为) o en el marco
# 称/以/视…为… ; en lo demás es la preposición wèi (为你高兴).
_WEI2_PREV = set("作成称视选认变改分译转化列评定当立任推封尊奉拜")
_WEI2_FRAME = {"称", "视", "选", "以", "尊", "奉", "拜", "封", "评", "推", "任命", "推选", "评选", "选举"}

# Tras estas negaciones, el 过 final de "verbo+过" es el aspecto (没穿过), no 过 "pasar".
_NEG_BEFORE_GUO = {"没", "没有", "还没", "从没", "从来没", "从未", "未", "还没有", "从来没有"}

_jieba_words: set[str] = set()


def _segment(run: str, fixed: dict[str, list[str]]) -> list[tuple[str, str]]:
    """Segmenta con jieba, al que se añaden las palabras con lectura fija
    (sílabo, excepciones) para que las reconozca como palabras."""
    import jieba
    import jieba.posseg as pseg

    for w in fixed.keys() - _jieba_words:
        if len(w) > 1:
            jieba.add_word(w)
        _jieba_words.add(w)
    return [(p.word, p.flag) for p in pseg.cut(run)]


def _fixed_overlay(word: str, fixed: dict[str, list[str]]) -> list[str | None]:
    """Lectura fija de cada carácter de `word`: la palabra entera si tiene lectura
    fija, o las palabras con lectura fija que contiene (衣服 dentro de 洗衣服)."""
    if word in fixed:
        return list(fixed[word])
    out: list[str | None] = [None] * len(word)
    i = 0
    while i < len(word):
        for n in range(len(word) - i, 1, -1):
            piece = word[i:i + n]
            if piece in fixed:
                out[i:i + n] = fixed[piece]
                i += n
                break
        else:
            i += 1
    return out


def _phrase_backs(word: str, i: int, numbered: str) -> bool:
    """¿Alguna palabra del diccionario (pypinyin + CC-CEDICT) dentro de `word`,
    que cubra la posición i, lee ese carácter como `numbered`? Si no, la lectura
    salió de la lectura por defecto del carácter, no de una palabra conocida."""
    from pypinyin.constants import PHRASES_DICT

    want = to_marks(numbered)
    for a in range(0, i + 1):
        for b in range(max(i + 1, a + 2), len(word) + 1):
            entry = PHRASES_DICT.get(word[a:b])
            if entry and len(entry) == b - a and want in entry[i - a]:
                return True
    return False


def _fixed_pieces(word: str, fixed: dict[str, list[str]], t_i: int) -> list[object]:
    """Para cada carácter, la palabra de lectura fija que lo cubre (misma lógica que _fixed_overlay)."""
    if word in fixed:
        return [(t_i, 0)] * len(word)
    out: list[object] = [None] * len(word)
    i = 0
    while i < len(word):
        for n in range(len(word) - i, 1, -1):
            if word[i:i + n] in fixed:
                out[i:i + n] = [(t_i, i)] * n
                i += n
                break
        else:
            i += 1
    return out


def _read_words(run: str, lexicon: dict[str, list[str]], single: dict[str, str] | None = None,
                in_compounds: bool = True) -> list[_Syl]:
    """Lee una secuencia de caracteres chinos, palabra por palabra."""
    fixed = {**_ZHAO_ZHUO, **_overrides(), **lexicon}  # el sílabo manda (R-CON-01)
    tokens = _segment(run, fixed)
    out: list[_Syl] = []
    for t_i, (word, flag) in enumerate(tokens):
        if single and word in single:
            overlay: list[str | None] = [single[word]]
            from_fixed = [None]
        else:
            overlay = _fixed_overlay(word, fixed)
            from_fixed = _fixed_pieces(word, fixed, t_i)
            if single and in_compounds and word not in fixed:
                # La lectura de la acepción también vale dentro de palabras que no son
                # del sílabo (好学 hàoxué); en las del sílabo (好吃) manda el sílabo.
                for i, ch in enumerate(word):
                    if ch in single and overlay[i] is None:
                        overlay[i] = single[ch]
        syls = _numbered(word)
        if len(syls) != len(word):  # salvaguarda: una sílaba por carácter
            syls = [_numbered(c)[0] for c in word]
        if single and not in_compounds and len(word) > 1 and word not in fixed:
            # Lectura del sílabo de la entrada dentro de un segmento que jieba unió pero
            # que el diccionario no conoce (重写 chóngxiě, 空房间 kòngfángjiān): el
            # carácter es la palabra objetivo. Si el diccionario respalda otra lectura
            # (天空 tiānkōng, 前边 qiánbian), manda el diccionario.
            for i, ch in enumerate(word):
                if ch in single and overlay[i] is None and syls[i] != single[ch] and (
                    not _phrase_backs(word, i, syls[i])
                    or _phrase_backs(word, i, single[ch])  # el diccionario admite las dos (好学)
                ):
                    overlay[i] = single[ch]
        prev_tok = tokens[t_i - 1] if t_i > 0 else ("", "")
        next_tok = tokens[t_i + 1] if t_i + 1 < len(tokens) else ("", "")
        for i, ch in enumerate(word):
            if overlay[i] is not None:
                syls[i] = overlay[i]
                continue
            if len(word) == 1 and flag in _PARTICLE_BY_POS and ch in "的地得着了":
                syls[i] = _PARTICLE_BY_POS[flag]
            if ch == "地":
                if len(word) == 1 and (prev_tok[1][:1] in ("r", "m", "q") or prev_tok[0][-1:] in "块片亩"):
                    syls[i] = "di4"  # sustantivo: 这块地, 一片地
                elif i >= 2 and word[i - 1] == word[i - 2]:
                    syls[i] = "de5"  # tras reduplicación: 哈哈地笑
            if ch == "为" and i > 0 and word[i - 1] in _WEI2_PREV and word not in fixed:
                syls[i] = "wei2"  # dentro del segmento: 被选为
            elif ch == "为" and len(word) == 1:
                before = [t for t, _ in tokens[:t_i]]
                if (prev_tok[0][-1:] in _WEI2_PREV
                        or any(t in _WEI2_FRAME for t in before)
                        or any(t == "所" for t, _ in tokens[t_i + 1:])):
                    syls[i] = "wei2"  # "como, en calidad de": 称他为…, 以…为…, 为…所…
            if ch == "着":
                syls[i] = "zhe5"
            # En las entradas 得 dé / děi, la palabra no es la partícula de aunque vaya en un
            # compuesto (得了 dé le): ahí manda el diccionario.
            if ch == "得" and word not in _DE2_WORDS and not (single and single.get("得", "de5") != "de5"):
                if len(word) == 1 and prev_tok[1][:1] in ("r", "n") and next_tok[1][:1] == "v":
                    syls[i] = "dei3"  # modal: 我得走了
                elif i > 0 or flag == "ud" or prev_tok[1][:1] in ("v", "a"):
                    syls[i] = "de5"   # partícula: 跑得快, 看得见, 病得很重
            if ch == "过" and word not in _GUO4_WORDS and (
                (len(word) == 1 and prev_tok[1][:1] in ("v", "a")       # 吃 过
                 and next_tok[1][:1] not in ("a", "d"))                  # pero 过快 = demasiado
                or (i == len(word) - 1 and i > 0 and flag[:1] == "v")    # 去过, 看过
            ):
                syls[i] = "guo5"  # partícula de experiencia
            elif (ch == "过" and 0 < i < len(word) - 1 and word not in _GUO4_WORDS
                  and not _phrase_backs(word, i, "guo4")):
                syls[i] = "guo5"  # dentro de un segmento sin palabra conocida: 当过兵, 打过仗
            if ch == "只":
                prev = word[i - 1] if i > 0 else (prev_tok[0][-1:] if prev_tok[0] else "")
                if prev in _ZHI_CLASSIFIER_PREV:
                    syls[i] = "zhi1"
        if (len(word) == 2 and word[1] == "过" and word not in _GUO4_WORDS
                and prev_tok[0] in _NEG_BEFORE_GUO):
            syls[1] = "guo5"  # 还没穿过 (aspecto), aunque 穿过 "atravesar" sea del sílabo
        if word == "得了" and prev_tok[1][:1] == "v" and next_tok[1][:1] not in ("n", "m", "q"):
            # Complemento potencial V得了 (de liǎo: 吃得了吗), no 得了 déle "obtener / basta".
            syls, from_fixed = ["de5", "liao3"], [None, None]
        elif (len(word) == 3 and word[1:] == "得了" and word not in fixed
              and word[:2] not in _DE2_WORDS):
            syls[1:], from_fixed[1:] = ["de5", "liao3"], [None, None]  # 吃得了 en un solo segmento
        for i, ch in enumerate(word):
            out.append(_Syl(ch, syls[i], word, i, from_fixed[i]))
    # 个 tras número o 几/半/每 conserva el cuarto tono; tras 这/那/哪 es neutro.
    for i, s in enumerate(out):
        if s.char == "个" and i > 0:
            prev = out[i - 1].char
            if prev in "这那哪":
                s.numbered = "ge5"
            elif prev in _DIGITS or prev in "几半每多":
                s.numbered = "ge4"
    return out


def _apply_yi_bu_sandhi(syls: list[_Syl]) -> None:
    for i, s in enumerate(syls):
        if s.char not in "一不":
            continue
        nxt = syls[i + 1] if i + 1 < len(syls) else None
        if s.char == "一" and s.fixed is not None and s.numbered == "yi1" and nxt and nxt.fixed == s.fixed:
            continue  # el sílabo escribe yī a propósito dentro de la palabra (一流 yīliú, 一一 yīyī)
        prev_c = syls[i - 1].char if i > 0 else ""
        next_c = syls[i + 1].char if i + 1 < len(syls) else ""
        # Tono de la sílaba siguiente tal como se lee aquí (不禁 bùjīn, no el jìn aislado);
        # si es átona, el de su lectura aislada.
        next_tone = _tone(nxt.numbered) if nxt and _tone(nxt.numbered) != 5 else (_base_tone(next_c) if next_c else 0)
        if s.char == "不":
            if _tone(s.numbered) == 5:
                continue  # el diccionario ya lo da neutro (对不起, 好不好)
            if prev_c and prev_c == next_c:  # A不A
                s.numbered = "bu5"
            elif next_c and next_tone == 4:
                s.numbered = "bu2"
            else:
                s.numbered = "bu4"
            continue
        # 一
        if _tone(s.numbered) == 5:
            continue
        if prev_c and prev_c == next_c and prev_c not in _DIGITS:  # V一V: 看一看
            s.numbered = "yi5"
        elif (
            not next_c
            or prev_c == "第"
            or next_c in _YI_KEEP_NEXT
            or any(w in s.word for w in _YI_KEEP_WORDS)
            or (prev_c in _DIGITS)
            or (next_c in _DIGITS and next_c not in "百千万亿")
        ):
            s.numbered = "yi1"
        else:
            s.numbered = "yi2" if next_tone in (4, 5) else "yi4"


def _merge_erhua(syls: list[_Syl]) -> list[tuple[str, str]]:
    """Devuelve pares (texto_original, sílaba_numerada) con el erhua fusionado."""
    out: list[tuple[str, str]] = []
    for i, s in enumerate(syls):
        if s.char == "儿" and out and i > 0:
            pair = syls[i - 1].char + "儿"
            full = pair in _FULL_ER_WORDS or (i + 1 < len(syls) and "儿" + syls[i + 1].char in _FULL_ER_WORDS)
            if not full and s.index_in_word > 0:
                chars, prev = out[-1]
                out[-1] = (chars + "儿", re.sub(r"([1-5])$", r"r\1", prev))
                continue
        out.append((s.char, s.numbered))
    return out


def to_marks(numbered: str) -> str:
    """'nv3' → 'nǚ', 'ma5' → 'ma', 'nar3' → 'nǎr'."""
    return to_tone(numbered.replace("v", "ü"))


def a_pinyin(
    text: str,
    lexicon: dict[str, list[str]] | None = None,
    target: tuple[str, str] | None = None,
    target_in_compounds: bool = True,
) -> str:
    """
    Pinyin canónico de una oración en chino.

    `lexicon` (palabra → sílabas numeradas) son las palabras del sílabo con
    su pinyin oficial (ver `syllabus_lexicon`): cuando una aparece en la
    oración, se usa su lectura del sílabo (R-CON-01).

    `target` = (palabra, lectura) fija la lectura de la palabra que ilustra el
    ejemplo en esa acepción, p. ej. ("好", "hào") para "ser aficionado a".
    """
    if not text:
        return ""
    _setup()
    lexicon = dict(lexicon or {})
    single: dict[str, str] = {}
    if target and target[1]:
        syls = split_word_pinyin(*target)
        if syls and len(target[0]) > 1:
            lexicon[target[0]] = syls
        elif syls:
            single[target[0]] = syls[0]  # solo cuando la palabra aparece sola, no dentro de otra (好看)
    # Palabra objetivo de dos caracteres que el ejemplo separa (理一次发, 停了车):
    # sus caracteres conservan la lectura del sílabo (发 fà, no fā).
    split_target: tuple[str, list[str]] | None = None
    if target and target[1] and len(target[0]) == 2 and target[0] not in text:
        syls_t = split_word_pinyin(*target)
        if syls_t:
            split_target = (target[0], syls_t)
    pieces: list[tuple[str, str]] = []  # (tipo, valor): "syl" | "punct" | "other"
    run = ""

    def flush():
        nonlocal run
        if run:
            syls = _read_words(run, lexicon, single, target_in_compounds)
            if split_target:
                (a, b), (sa, sb) = split_target
                i = run.find(a)
                j = run.find(b, i + 2) if i >= 0 else -1
                if i >= 0 and 0 < j - i <= 5:
                    syls[i].numbered, syls[j].numbered = sa, sb
            _apply_yi_bu_sandhi(syls)
            for _, num in _merge_erhua(syls):
                pieces.append(("syl", to_marks(num)))
            run = ""

    prev_ch_other = False
    for ch in text:
        if is_chinese_char(ch):
            run += ch
            prev_ch_other = False
            continue
        flush()
        if ch in CHINESE_PUNCTUATION:
            pieces.append(("punct", ch))
        elif ch.isspace():
            continue
        elif pieces and pieces[-1][0] == "other" and prev_ch_other:
            pieces[-1] = ("other", pieces[-1][1] + ch)  # "10" se mantiene junto
        else:
            pieces.append(("other", ch))
        prev_ch_other = not (ch in CHINESE_PUNCTUATION or ch.isspace())
    flush()

    out = ""
    prev_kind, prev_val = "", ""
    for kind, val in pieces:
        if kind == "punct":
            mapped = CHINESE_PUNCTUATION[val]
            if val in _OPENING:
                out += (" " if out else "") + mapped
            else:
                out += mapped
        else:
            glue = (prev_kind == "punct" and prev_val in _OPENING) or not out
            out += ("" if glue else " ") + val
        prev_kind, prev_val = kind, val
    return out.strip()


# ---------------------------------------------------------------------------
# Comprobación sílaba a sílaba (validación `example_pinyin_matches`)
# ---------------------------------------------------------------------------

_SYL_RE = re.compile(r"[a-zA-ZüÜāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜńňǹḿ]+")


def split_syllables(pinyin_text: str) -> list[str]:
    """Sílabas de un texto en formato canónico, en minúsculas y numeradas."""
    return [to_tone3(t.lower(), neutral_tone_with_five=True) or t.lower()
            for t in _SYL_RE.findall(pinyin_text)]


@lru_cache(maxsize=None)
def readings(char: str) -> frozenset[str]:
    """Lecturas posibles de un carácter (todas las del diccionario + su tono neutro)."""
    _setup()
    base = _pypinyin(char, style=Style.TONE3, heteronym=True, neutral_tone_with_five=True)[0]
    out = set()
    for r in base:
        out.add(r)
        out.add(_with_tone(r, 5))
    if char == "一":
        out |= {"yi1", "yi2", "yi4", "yi5"}
    if char == "不":
        out |= {"bu2", "bu4", "bu5"}
    return frozenset(out)


def split_word_pinyin(hanzi: str, syllabus_pinyin: str) -> list[str] | None:
    """
    Reparte el pinyin del sílabo de una palabra en una sílaba numerada por
    carácter: ("那边", "nàbiān") → ["na4", "bian1"]; ("一点儿", "yìdiǎnr") →
    ["yi4", "dian3", "er5"]. Si hay variantes ("shéi/shuí") usa la primera.
    Devuelve None si no logra repartirlo.
    """
    if not syllabus_pinyin:
        return None
    text = syllabus_pinyin.split("/")[0].lower()
    text = re.sub(r"[\s'’‘·\-]", "", text)
    chars = list(hanzi)
    if not all(is_chinese_char(c) for c in chars):
        return None

    candidates = {c: sorted({to_marks(r) for r in readings(c)} | {to_marks(r).replace("ü", "v") for r in readings(c)}, key=len, reverse=True) for c in chars}

    def solve(ci: int, pos: int) -> list[str] | None:
        if ci == len(chars):
            return [] if pos == len(text) else None
        ch = chars[ci]
        if ch == "儿" and ci > 0 and text[pos:pos + 1] == "r" and not text.startswith("er", pos):
            rest = solve(ci + 1, pos + 1)
            if rest is not None:
                return ["er5"] + rest
        for cand in candidates[ch]:
            if text.startswith(cand, pos):
                rest = solve(ci + 1, pos + len(cand))
                if rest is not None:
                    num = to_tone3(cand.replace("v", "ü"), neutral_tone_with_five=True)
                    return [num] + rest
        return None

    return solve(0, 0)


def syllabus_lexicon(entries) -> dict[str, list[str]]:
    """Construye el léxico para `a_pinyin` a partir de pares (hanzi, pinyin del sílabo).
    Solo palabras de dos o más caracteres: en las de uno, la lectura depende de la
    oración (好 hǎo / hào) y se resuelve con el diccionario y las reglas."""
    lex = {}
    for hanzi, syllabus_pinyin in entries:
        if len(hanzi) < 2:
            continue
        syls = split_word_pinyin(hanzi, syllabus_pinyin)
        if syls and hanzi not in lex:  # gana la primera (nivel más bajo)
            lex[hanzi] = syls
    return lex


def pinyin_mismatches(zh: str, pinyin_text: str) -> list[str]:
    """
    Compara un ejemplo con su pinyin. Devuelve la lista de problemas (vacía si
    todo cuadra): cada carácter chino debe tener una sílaba que sea una de sus
    lecturas; 儿 puede ir fusionado como erhua con la sílaba anterior.
    """
    chars = [c for c in zh if is_chinese_char(c)]
    syls = split_syllables(pinyin_text)
    problems: list[str] = []
    ci = si = 0
    while ci < len(chars) and si < len(syls):
        ch, syl = chars[ci], syls[si]
        erhua = (
            ci + 1 < len(chars) and chars[ci + 1] == "儿"
            and re.search(r"r[1-5]$", syl) and not syl.startswith("er")
        )
        if erhua:
            base = re.sub(r"r([1-5])$", r"\1", syl)
            if base not in readings(ch):
                problems.append(f"'{ch}' no se lee '{to_marks(syl)}'")
            ci += 2
            si += 1
            continue
        if syl not in readings(ch):
            problems.append(f"'{ch}' no se lee '{to_marks(syl)}'")
        ci += 1
        si += 1
    if ci < len(chars) or si < len(syls):
        problems.append(
            f"{len(chars)} caracteres y {len(syls)} sílabas no se corresponden "
            "(una sílaba por carácter, separadas por espacio)"
        )
    return problems
