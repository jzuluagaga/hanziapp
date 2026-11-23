"""
Lectura del texto (pdftotext -layout) de las listas "New HSK Vocabulary" de
Mandarin Bean. Produce el formato de `load_syllabus`: hanzi, pinyin y orden
(dato del sílabo) más las glosas en inglés como glosas de terceros, que solo
se usan internamente (R-CON-02).

Cada glosa empareja una categoría con un tramo de la traducción; lo que va
entre paréntesis en la lista es un uso secundario.
"""
import re

_POS_WORDS = {
    "noun", "verb", "adjective", "adverb", "pronoun", "preposition", "conjunction", "classifier",
    "auxiliary", "number", "numberclassifier", "number-classifier", "suffix", "prefix", "interjection", "拟声",
    # Level 6 usa las abreviaturas chinas
    "名", "动", "形", "副", "量", "介", "连", "代", "助", "叹", "后缀", "前缀", "数", "数量",
}
_CJK_POS_TAIL = re.compile(r"^(.*?[a-zāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜü]) ?((?:名|动|形|副|量|介|连|代|助|叹)(?:、(?:名|动|形|副|量|介|连|代|助|叹))*)$")
_ENTRY = re.compile(r"^\s*(\d{1,4})\s{2,}(\S+)\s{2,}(.*)$")


def _is_pos(text: str) -> bool:
    words = [w for w in re.split(r"[、（）()\s]+", text) if w]
    return bool(words) and all(w in _POS_WORDS for w in words)


def _top_level_split(text: str, seps: str) -> list[str]:
    parts, depth, cur = [], 0, ""
    for ch in text:
        if ch in "（(":
            depth += 1
        elif ch in "）)":
            depth -= 1
        if ch in seps and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return [p.strip() for p in parts if p.strip()]


def _unwrap(text: str) -> tuple[str, bool]:
    """'(measure word)' → ('measure word', True). Devuelve (texto, era_secundaria)."""
    t = text.strip()
    if t[:1] in "（(" and t[-1:] in "）)":
        return t[1:-1].strip(), True
    return t, False


def _balance(text: str) -> str:
    """Quita un paréntesis de cierre sin apertura (errata del PDF: 'the phone)')."""
    if text.count(")") > text.count("(") and text.endswith(")"):
        return text[:-1].rstrip()
    return text


def _glosses(pos_raw: str, translation: str) -> list[dict]:
    # Errata del PDF (Level 6): "verb" reemplazado por 动 dentro del inglés ("used after 动s", "动al").
    translation = re.sub(r"动(?=[a-z])", "verb", _balance(translation))
    pos_groups = _top_level_split(pos_raw, "、") if pos_raw else []
    tr_groups = _top_level_split(translation, ";；")
    # Errata del PDF (Level 5): la categoría "classifier" falta y deja el hueco
    # ("、noun", "verb、adjective、"). Si los huecos cuadran con la traducción y
    # esa parte es un clasificador ("measure word …"), se rellena.
    if pos_raw and "、" in pos_raw:
        raw = [p.strip() for p in re.split(r"、(?![^（(]*[）)])", pos_raw)]
        if "" in raw and len(raw) == len(tr_groups):
            filled = [p or ("classifier" if t.lower().startswith("measure word") else "")
                      for p, t in zip(raw, tr_groups)]
            if all(filled):
                pos_groups = filled
    pairs = []
    if pos_groups and len(pos_groups) == len(tr_groups):
        for p, t in zip(pos_groups, tr_groups):
            p_in, p_sec = _unwrap(p)
            t_in, t_sec = _unwrap(t)
            secondary = p_sec or t_sec
            inner_p = _top_level_split(p_in, "、")
            inner_t = _top_level_split(t_in, ";；")
            if len(inner_p) > 1 and len(inner_p) == len(inner_t):
                pairs.extend((ip, it, not secondary) for ip, it in zip(inner_p, inner_t))
            else:
                pairs.append((p_in, t_in, not secondary))
    else:
        pairs.append((pos_raw, translation.strip(), True))
    return [
        {"sense_index": i, "pos_raw": p, "translation_en": t, "is_primary": primary}
        for i, (p, t, primary) in enumerate(pairs) if t
    ]


# Erratas del PDF en la columna de la palabra (Level 5, n.º 683: "劳verb" por 劳动).
_HANZI_ERRATA = {"劳verb": "劳动"}

_SEG = re.compile(r"\S+(?: \S+)*")  # campos separados por dos o más espacios


def _segments(line: str) -> list[tuple[int, str]]:
    return [(m.start(), m.group()) for m in _SEG.finditer(line)]


def parse_layout_text(text: str, hsk_level: int) -> list[dict]:
    """
    Cada fila empieza con número, palabra y pinyin; categoría y traducción
    pueden partirse en varias líneas. Los trozos de las líneas siguientes se
    asignan a la columna más cercana por posición (pinyin "Zhōnghuá / Mínzú",
    categoría "number- / classifier、noun"), no por su contenido.
    """
    entries, cur = [], None
    cols = {"pinyin": None, "pos": None, "tr": None}
    for line in text.splitlines():
        if not line.strip() or "MandarinBean.com" in line or line.strip().startswith(("NO.", "NEW HSK", "Level", "ENTRIES")):
            continue
        m = _ENTRY.match(line)
        if m and re.match(r"[一-鿿]", m.group(2)):
            segs = _segments(line)[2:]  # sin número ni palabra
            (cols["pinyin"], pinyin), rest = segs[0], segs[1:]
            glued = _CJK_POS_TAIL.match(pinyin)  # "fāngfāngmiànmiàn名": pinyin y categoría sin espacio
            if glued:
                pinyin = glued.group(1)
                rest = [(cols["pinyin"] + len(glued.group(0)) - len(glued.group(2)), glued.group(2))] + rest
            pos, tr = "", []
            if rest:
                start, first = rest[0]
                if len(rest) > 1 or _is_pos(first):
                    pos, tr = first, [t for _, t in rest[1:]]
                    cols["pos"] = start
                    if len(rest) > 1:
                        cols["tr"] = rest[1][0]
                else:
                    # Categoría larga pegada a la traducción con un solo espacio ("numberclassifier、 once").
                    head, _, tail = first.partition(" ")
                    if _is_pos(head):
                        pos, tr = head, [tail]
                    else:
                        tr = [first]
                        cols["tr"] = start
            hanzi = _HANZI_ERRATA.get(m.group(2), m.group(2))
            hanzi = re.sub(r"\d+$", "", hanzi)  # 花2 → 花 (homógrafo numerado)
            if not all(re.match(r"[一-鿿]", c) for c in hanzi):
                raise ValueError(f"n.º {m.group(1)}: palabra ilegible en el PDF: {m.group(2)!r}")
            cur = {
                "no": int(m.group(1)),
                "simplified": hanzi,
                "pinyin_pdf": pinyin,
                "hsk_level": hsk_level,
                "_pos": pos,
                "_tr": " ".join(tr),
            }
            entries.append(cur)
            continue
        if cur is None:
            continue
        for start, seg in _segments(line):
            known = {k: v for k, v in cols.items() if v is not None}
            col = min(known, key=lambda k: abs(start - known[k])) if known else "tr"
            if col == "pos" and not _is_pos(seg.replace("-", "")) and not _is_pos(seg):
                col = "tr"
            if col == "pinyin":
                cur["pinyin_pdf"] += ("" if cur["pinyin_pdf"].endswith("-") else " ") + seg
            elif col == "pos":
                cur["_pos"] += seg
            else:
                cur["_tr"] = (cur["_tr"] + " " + seg).strip()
    for e in entries:
        e["senses"] = _glosses(e.pop("_pos"), e.pop("_tr"))
    return entries
