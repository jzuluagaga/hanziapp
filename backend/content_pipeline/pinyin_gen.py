"""
pinyin_gen.py
Generación determinista de pinyin para palabras y frases completas usando pypinyin.
Aplica reglas de sandhi tonal para 不 (bù) y 一 (yī), y fusiona erhua (儿) con la
sílaba anterior.

Principio de diseño: el pinyin NUNCA lo genera el LLM. Lo fonético se resuelve
con reglas deterministas; lo semántico (traducciones, frases) se le pide al
modelo. Esta función se usa tanto para el pinyin de palabras sueltas como para
el pinyin de las frases de ejemplo generadas por batch_runner.py.
"""
import re
from pypinyin import pinyin, Style

# Puntuación china que no debe llevar espacio antes en el pinyin renderizado
_NO_SPACE_BEFORE = set("，。！？、；：）》")
_NO_SPACE_AFTER = set("（《")

# 儿 es léxicamente ambiguo: a veces es un morfema completo ("hijo/a", tono
# propio 'ér'), y a veces es sufijo de erhua fusionado con la sílaba anterior
# (哪儿 nǎr, 这儿 zhèr). No se puede resolver solo por posición — se necesita
# una lista de excepciones conocidas. Lista curada a partir del vocabulario
# real de HSK1; ampliar si aparecen casos nuevos en niveles superiores.
_NOT_ERHUA_PREFIX = {"儿子", "儿童", "儿科"}  # 儿 + siguiente char = palabra completa
_NOT_ERHUA_SUFFIX = {"女儿", "婴儿", "孤儿"}  # char anterior + 儿 = palabra completa


def _tone_of_numbered(syll_numbered: str) -> int:
    """Extrae el número de tono de una sílaba en formato numerado (ej. 'si4' -> 4). 5 = neutro."""
    m = re.search(r"([1-5])$", syll_numbered)
    return int(m.group(1)) if m else 5


def _is_chinese_char(ch: str) -> bool:
    return "\u4e00" <= ch <= "\u9fff"


def a_pinyin(text: str) -> str:
    """
    Genera el pinyin tonal (con marcas diacríticas, ej. 'nǐ hǎo') de una frase
    completa en chino. Aplica sandhi de 不/一 y fusiona 儿 (erhua) con la sílaba
    anterior. Caracteres no chinos (puntuación, números arábigos, letras) se
    conservan tal cual.
    """
    if not text:
        return ""

    chars = list(text)
    n = len(chars)

    # pypinyin por carácter, para poder aplicar sandhi mirando el vecino
    numbered = pinyin(text, style=Style.TONE3, heteronym=False, neutral_tone_with_five=True)
    tonal = pinyin(text, style=Style.TONE, heteronym=False)

    pieces = []
    i = 0
    while i < n:
        ch = chars[i]

        if not _is_chinese_char(ch):
            # Erhua: 儿 no es chino-estándar aquí porque SÍ lo es; este branch
            # es para puntuación/latín/números, que pypinyin devuelve tal cual.
            pieces.append(("punct", ch))
            i += 1
            continue

        if ch == "儿":
            prefix_word = chars[i] + chars[i + 1] if i + 1 < n else ""
            suffix_word = chars[i - 1] + chars[i] if i > 0 else ""
            is_full_morpheme = (
                prefix_word in _NOT_ERHUA_PREFIX or suffix_word in _NOT_ERHUA_SUFFIX
            )
            if not is_full_morpheme and pieces and pieces[-1][0] == "syll":
                # Fusiona erhua con la sílaba anterior sin espacio, agregando 'r'
                prev_type, prev_val = pieces[-1]
                pieces[-1] = ("syll", prev_val + "r")
                i += 1
                continue
            # Si no, 儿 se trata como sílaba propia más abajo (tono 'ér' normal)

        current_tonal = tonal[i][0] if i < len(tonal) else ch

        # --- Sandhi de 不 (bù) ---
        if ch == "不" and i + 1 < n and i + 1 < len(numbered):
            next_tone = _tone_of_numbered(numbered[i + 1][0])
            if next_tone == 4:
                current_tonal = "bú"
            else:
                current_tonal = "bù"

        # --- Sandhi de 一 (yī) ---
        elif ch == "一" and i + 1 < n and i + 1 < len(numbered):
            next_tone = _tone_of_numbered(numbered[i + 1][0])
            if next_tone == 4:
                current_tonal = "yí"
            elif next_tone in (1, 2, 3):
                current_tonal = "yì"
            # next_tone == 5 (neutro, ej. número ordinal/fecha): se deja yī
            # por defecto (heurística conservadora, revisar casos reales).

        pieces.append(("syll", current_tonal))
        i += 1

    # Ensamblar con espacios entre sílabas, sin espacio antes de puntuación china
    out = []
    for idx, (kind, val) in enumerate(pieces):
        if idx == 0:
            out.append(val)
            continue
        prev_kind, prev_val = pieces[idx - 1]
        if val and val[0] in _NO_SPACE_BEFORE:
            out.append(val)
        elif prev_val and prev_val[-1] in _NO_SPACE_AFTER:
            out.append(val)
        else:
            out.append(" " + val)

    return "".join(out).strip()


if __name__ == "__main__":
    tests = [
        "我不去",
        "一个人",
        "不客气",
        "他儿子在这儿。",
        "你好吗？",
        "这是一本书。",
        "一天一天地过去了。",
    ]
    for t in tests:
        print(f"{t}  ->  {a_pinyin(t)}")
