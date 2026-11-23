"""
Catálogo de categorías gramaticales. Son claves, no textos: el nombre visible
se resuelve por idioma en los catálogos de interfaz (R-IDI-09).
"""

POS_KEYS = [
    "noun", "verb", "adjective", "adverb", "pronoun", "numeral", "classifier",
    "numeral_classifier", "particle", "preposition", "conjunction",
    "interjection", "prefix", "suffix", "phrase",
]

POS_CHOICES = [(k, k) for k in POS_KEYS]

# Categorías de la fuente de glosas → clave del catálogo. Las combinadas
# ("verb、classifier") o vacías no se adivinan: quedan sin categoría y la
# validación `sense_count` obliga a revisarlas.
_SOURCE_MAP = {
    "noun": "noun", "verb": "verb", "adjective": "adjective", "adverb": "adverb",
    "pronoun": "pronoun", "number": "numeral", "numeral": "numeral",
    "classifier": "classifier", "measure word": "classifier",
    "number-classifier": "numeral_classifier", "numberclassifier": "numeral_classifier",
    "auxiliary": "particle", "particle": "particle", "preposition": "preposition",
    "conjunction": "conjunction", "interjection": "interjection",
    "prefix": "prefix", "suffix": "suffix", "phrase": "phrase",
    "拟声": "interjection",  # onomatopeya (哈): el catálogo no tiene una clave propia
    # Abreviaturas chinas (lista Level 6)
    "名": "noun", "动": "verb", "形": "adjective", "副": "adverb", "量": "classifier",
    "介": "preposition", "连": "conjunction", "代": "pronoun", "助": "particle", "叹": "interjection",
    "后缀": "suffix", "前缀": "prefix", "数": "numeral", "数量": "numeral_classifier",
}

# Categorías cuyo significado explica el uso (08-contenido.md §4, punto 2).
FUNCTION_POS = {"classifier", "numeral_classifier", "particle", "prefix", "suffix"}


def normalize_pos(raw: str) -> str:
    return _SOURCE_MAP.get((raw or "").strip().lower(), "")
