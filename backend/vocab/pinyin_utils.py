"""Conversión de pinyin con tildes (dato ya revisado a mano en el JSON) a
pinyin numerado, para Word.pinyin_numbered.

Deliberadamente NO se regenera desde el hanzi vía pypinyin: eso reintroduce
el error de tono neutro y de caracteres polisémicos (觉, 好, 只...) que ya se
corrigió en el pinyin con tildes. En su lugar, se alinea el pinyin con
tildes ya correcto contra el hanzi, usando pypinyin solo para saber cuántas
letras ocupa cada sílaba (no para saber el tono).
"""
from pypinyin import pinyin, Style

_TONE_MAP = {}
for _base, _tones in [
    ('a', 'āáǎà'), ('e', 'ēéěè'), ('i', 'īíǐì'),
    ('o', 'ōóǒò'), ('u', 'ūúǔù'), ('v', 'ǖǘǚǜ'),
    ('n', 'ńňǹ'), ('m', 'ḿ'),
]:
    for _tone_num, _ch in enumerate(_tones, 1):
        _TONE_MAP[_ch] = (_base, _tone_num)

# 觉 es polisémico (jué "sentir" vs jiào "dormir"); pypinyin da por defecto
# 'jue' (3 letras). En 睡觉 la lectura real es 'jiao' (4 letras), lo que
# rompe la alineación por longitud. Único caso detectado en HSK1.
_LEN_OVERRIDE = {
    ('睡觉', 1): 4,
}


def _base_len(hanzi_char):
    return len(pinyin(hanzi_char, style=Style.NORMAL)[0][0])


def tonal_to_numbered(hanzi, pinyin_tonal):
    """Convierte 'māma' -> 'ma1ma5', 'nǚ\\'ér' -> 'nv3er2', etc.

    Devuelve None si el pinyin con tildes no se pudo alinear letra a letra
    contra el hanzi (para no adivinar un resultado incorrecto en silencio).
    """
    chars = list(hanzi)
    has_apostrophe = ("'" in pinyin_tonal) or ("’" in pinyin_tonal)
    s = pinyin_tonal.replace("'", "").replace("’", "")
    pos = 0
    out = []
    for i, c in enumerate(chars):
        if (hanzi, i) in _LEN_OVERRIDE:
            n = _LEN_OVERRIDE[(hanzi, i)]
        elif c == '儿' and i == len(chars) - 1 and i > 0 and not has_apostrophe:
            n = 1  # erhua real: 儿 se fusiona como 'r' suelto
        else:
            n = _base_len(c)
        chunk = s[pos:pos + n]
        pos += n
        if len(chunk) != n:
            return None
        tone = 5
        letters = []
        for ch in chunk:
            if ch in _TONE_MAP:
                base, tone = _TONE_MAP[ch]
                letters.append(base)
            else:
                letters.append(ch)
        out.append(''.join(letters) + str(tone))
    if pos != len(s):
        return None
    return ''.join(out)
