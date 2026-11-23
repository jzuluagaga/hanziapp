"""
validators.py
Suite de validadores de calidad para el contenido HSK generado (meaning_es +
examples). Corre sobre el JSON de records producido por batch_runner.py /
retry_failed.py, separa lo limpio de lo que necesita revisión, y arma
review_queue.json ordenado por severidad (ALTO > MEDIO > BAJO).

Uso:
    python validators.py review_queue_raw.json
"""
import json
import argparse
import re
from difflib import SequenceMatcher

try:
    import langid

    langid.set_languages(["es", "en"])  # Restringido a es/en: reduce falsos
    # positivos frente al set completo de idiomas de langid (ej. detecta
    # frases cortas en español como catalán/gallego/italiano si no se acota).
    HAS_LANGID = True
except ImportError:
    HAS_LANGID = False

# Similitud máxima permitida (0-1) entre 2 frases de ejemplo de la misma
# acepción antes de marcarlas como "colapso de plantilla" (el modelo repitiendo
# casi la misma frase 3 veces). Ajustar si se ven muchos falsos positivos al
# escalar a vocabulario donde las frases naturales tienden a parecerse más.
DIVERSITY_THRESHOLD = 0.75

# langid es confiable en frases largas, pero da MUCHOS falsos positivos con
# palabras sueltas en español (ej. "libro", "ocho", "comer" se detectan como
# inglés). Probado empíricamente: por debajo de este número de caracteres,
# no usamos langid para meaning_es y en su lugar comparamos contra
# translation_en directamente (ver validar_fuga_ingles).
LANGID_MIN_CHARS = 15

# Palabras función en inglés a ignorar al extraer "palabras de contenido" de
# translation_en (no tiene sentido comparar contra "to", "a", "of", etc.)
# Nota: se excluyen aquí incluso palabras cortas de 2 letras (in, on, is, as,
# it) porque SÍ queremos detectar verbos de contenido cortos como "do".
_EN_STOPWORDS = {
    "to", "a", "an", "the", "of", "in", "on", "for", "or", "and", "one",
    "some", "with", "used", "measure", "word", "indicating", "is", "as",
    "at", "it", "be", "by",
}

SEVERITY_ORDER = {"ALTO": 0, "MEDIO": 1, "BAJO": 2}


def _is_chinese_char(ch: str) -> bool:
    return "\u4e00" <= ch <= "\u9fff"


def validar_cantidad_ejemplos(record: dict) -> list[tuple[str, str]]:
    n = len(record.get("examples", []))
    if n != 3:
        return [("ALTO", f"se esperaban 3 ejemplos, hay {n}")]
    return []


def validar_hanzi(record: dict) -> list[tuple[str, str]]:
    """Verifica que el hanzi objetivo aparezca literalmente en cada frase."""
    issues = []
    hanzi = record["hanzi"]
    for i, ex in enumerate(record.get("examples", [])):
        if hanzi not in ex.get("zh", ""):
            issues.append(("ALTO", f"ejemplo {i}: no contiene la palabra objetivo '{hanzi}'"))
    return issues


def validar_caracteres_zh(record: dict) -> list[tuple[str, str]]:
    """Verifica que sentence_zh no tenga letras latinas sueltas coladas."""
    issues = []
    for i, ex in enumerate(record.get("examples", [])):
        for ch in ex.get("zh", ""):
            if ch.isalpha() and not _is_chinese_char(ch):
                issues.append(("MEDIO", f"ejemplo {i}: carácter latino inesperado en zh: '{ch}'"))
                break
    return issues


def validar_fuga_ingles(record: dict) -> list[tuple[str, str]]:
    """
    Detecta si meaning_es literalmente contiene una palabra de contenido de
    translation_en (ej. meaning_es="love" cuando translation_en="to love").
    Más preciso que langid para textos cortos, donde langid falla mucho
    (confirmado empíricamente: "libro", "ocho", "comer" se detectan como
    inglés con alta confianza aunque son español correcto).
    """
    translation_en = record.get("translation_en", "")
    meaning_es = record.get("meaning_es", "")
    if not translation_en or not meaning_es:
        return []

    content_words = {
        w for w in re.findall(r"[a-zA-Z]+", translation_en.lower())
        if w not in _EN_STOPWORDS and len(w) >= 2
    }
    meaning_words = set(re.findall(r"[a-zA-Z]+", meaning_es.lower()))

    leaked = content_words & meaning_words
    if leaked:
        return [
            (
                "ALTO",
                f"meaning_es ('{meaning_es}') comparte palabra(s) en inglés con "
                f"translation_en ('{translation_en}'): {', '.join(sorted(leaked))}",
            )
        ]
    return []


def validar_idioma_es(record: dict) -> list[tuple[str, str]]:
    """Verifica que sentence_es (frases completas, donde langid SÍ es confiable)
    esté realmente en español."""
    if not HAS_LANGID:
        return []
    issues = []
    for i, ex in enumerate(record.get("examples", [])):
        es_text = ex.get("es", "")
        if len(es_text) < LANGID_MIN_CHARS:
            continue  # muy corto para que langid sea confiable
        lang, conf = langid.classify(es_text)
        if lang != "es":
            issues.append(
                ("ALTO", f"ejemplo {i}.es parece '{lang}' (conf={conf:.2f}): {es_text[:50]}")
            )
    return issues


def validar_diversidad(record: dict) -> list[tuple[str, str]]:
    """Detecta colapso de plantilla: frases de ejemplo demasiado parecidas."""
    issues = []
    examples = record.get("examples", [])
    for i in range(len(examples)):
        for j in range(i + 1, len(examples)):
            ratio = SequenceMatcher(None, examples[i]["zh"], examples[j]["zh"]).ratio()
            if ratio > DIVERSITY_THRESHOLD:
                issues.append(
                    ("MEDIO", f"ejemplos {i} y {j} muy similares (similitud={ratio:.2f})")
                )
    return issues


def validar_longitud(record: dict, min_chars: int = 4, max_chars: int = 40) -> list[tuple[str, str]]:
    issues = []
    for i, ex in enumerate(record.get("examples", [])):
        n = len(ex.get("zh", ""))
        if n < min_chars:
            issues.append(("BAJO", f"ejemplo {i}: frase muy corta ({n} caracteres)"))
        elif n > max_chars:
            issues.append(("BAJO", f"ejemplo {i}: frase muy larga ({n} caracteres)"))
    return issues


VALIDATORS = [
    validar_cantidad_ejemplos,
    validar_hanzi,
    validar_caracteres_zh,
    validar_fuga_ingles,
    validar_idioma_es,
    validar_diversidad,
    validar_longitud,
]


def validate_record(record: dict) -> list[tuple[str, str]]:
    issues = []
    for validator in VALIDATORS:
        issues.extend(validator(record))
    return issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("--out", default="review_queue.json")
    parser.add_argument("--clean-out", default="clean_records.json")
    args = parser.parse_args()

    with open(args.input_json, encoding="utf-8") as f:
        records = json.load(f)

    clean = []
    flagged = []

    for record in records:
        issues = validate_record(record)
        if not issues:
            clean.append(record)
        else:
            worst = min(issues, key=lambda x: SEVERITY_ORDER[x[0]])
            flagged.append(
                {
                    "record": record,
                    "issues": [{"severity": s, "detail": d} for s, d in issues],
                    "worst_severity": worst[0],
                }
            )

    flagged.sort(key=lambda x: SEVERITY_ORDER[x["worst_severity"]])

    with open(args.clean_out, "w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False, indent=2)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(flagged, f, ensure_ascii=False, indent=2)

    print(f"Total: {len(records)}")
    print(f"Limpios: {len(clean)} -> {args.clean_out}")
    print(f"Con banderas: {len(flagged)} -> {args.out}")
    by_severity: dict[str, int] = {}
    for item in flagged:
        by_severity[item["worst_severity"]] = by_severity.get(item["worst_severity"], 0) + 1
    for sev in ("ALTO", "MEDIO", "BAJO"):
        if sev in by_severity:
            print(f"  {sev}: {by_severity[sev]}")


if __name__ == "__main__":
    main()
