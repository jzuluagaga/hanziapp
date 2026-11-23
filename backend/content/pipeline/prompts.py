"""
Prompts y esquemas de salida para `generate_drafts`. No dependen del idioma:
el idioma de estudio, su variedad y su estilo vienen de la tabla de idiomas
(R-IDI-10: añadir un idioma no exige cambiar código).

Dos modos (08-contenido.md §2 y §8):
- full: acepciones y ejemplos en chino (base) + significados y traducciones.
- translate: sobre una base ya existente, solo significados y traducciones.

El modelo nunca escribe pinyin de los ejemplos: se calcula después.
"""
from __future__ import annotations

from ..pos import POS_KEYS

PROMPT_VERSION = "2026-11-22.5"


def _language_block(language_name: str, style: str) -> str:
    style_line = f"\n- Variety and style: {style}" if style.strip() else ""
    return (
        f"Target language for meanings and translations: {language_name}."
        f"{style_line}"
    )


_MEANING_RULES = """\
Meaning of each sense (written in the target language)
- Give what a learner at this level needs, not a dictionary definition: one to four words, or a few synonyms separated by "; ".
- No grammatical labels or notes in parentheses: the grammatical category is shown separately.
- Classifiers, particles, prefixes and suffixes: say in a few plain words, in your own words, what the word does in a sentence, without a grammatical label such as "particle" or "classifier". For the classifier 本, a short phrase meaning "used to count books and notebooks"; for 吧, one meaning "at the end of a sentence: suggests something or asks for agreement".
- Write every meaning entirely in the target language: the descriptions quoted above only illustrate the idea.
- The meaning must fit the example sentences of that sense exactly."""

_GLOSS_RULES = """\
Reference glosses
- You receive glosses written in English by a third party. They are internal references, never shown to learners. Use them only to know which meanings to cover. Never copy, translate word for word or closely paraphrase their wording: write in your own words."""


def full_system_prompt(language_name: str, style: str, level: int, allowed_words: list[str],
                       max_chars: int, tolerance: int) -> str:
    vocab = "、".join(allowed_words)
    return f"""You write study content for HanziApp, a Mandarin Chinese course for learners preparing the HSK exam (2025 syllabus). A human editor reviews everything you write before learners see it, so be accurate rather than creative.

{_language_block(language_name, style)}

For one HSK {level} word you write its senses. For each sense:
- source_gloss: the number of the reference gloss it covers, or -1 if none.
- pos: its grammatical category, one of: {", ".join(POS_KEYS)}.
- reading: the pinyin (tone marks) of the word in this sense ONLY if it differs from the syllabus pinyin given to you, e.g. 好 read "hào" in the sense "to be fond of", 只 read "zhǐ" in the sense "only". Otherwise an empty string.
- meaning: the meaning in the target language.
- examples: exactly 3 example sentences in Chinese, each with its translation into the target language.

{_GLOSS_RULES}
- Normally write one sense per reference gloss, in the same order. If a gloss mixes two grammatical categories (for example "verb、classifier"), write one sense per category, both pointing to that gloss. Merge glosses that are the same meaning.
- If the message lists other syllabus entries written with the same characters, each of them is a separate card: do not add senses that belong only to those entries.
- Add a sense that no gloss covers only if it is a common everyday use at this level that a learner would otherwise miss (source_gloss = -1).
- Put the most common everyday sense first. Glosses marked "secondary" are real but less frequent uses: give them sentences that reflect how that use is really said, even if more formal.
- Every sense must be read with the syllabus pinyin given to you (or its own reading field). Leave out a gloss that describes a use pronounced differently: for 得了 déle, "after a verb to express possibility" is 吃得了 de liǎo, another word.
- Leave out a gloss whose use, in modern Chinese, only lives inside longer words or set phrases (for a single character: a use that never appears with the character standing on its own). A human editor reviews every card and can add it back; an unnatural sentence is worse than a missing sense. Never leave the card empty: always write at least one sense, the most common way the word is used on its own (for 社, "agency, office" as in 社里).

{_MEANING_RULES}

Example sentences
- Natural, grammatical sentences a native speaker would really say, using the word clearly in that sense. Each sentence must make sense and be true or plausible in real life (no odd claims such as "drinking too much water is good for you").
- Each sense's sentences must show that sense and not another one of the same word: if two senses look alike (a preposition and a verb, for example), use structures that only fit the sense being illustrated.
- If the sense has its own reading, the word must keep that reading in every sentence: do not let it form a common word with another reading or meaning (for 好 read "hào", avoid 好吃, 好看, 好玩儿, which are read hǎo and mean something else).
- The word must appear in every sentence exactly as written, without splitting it or changing its characters. It must work as a word on its own in that sense, not only as a character inside a longer word: do not illustrate 重 "again" with 重新, or 生 with 生怕 or 生病; those are other words.
- Short and simple: one clause, at most {max_chars} Chinese characters, not counting punctuation.
- Vocabulary: apart from the target word, use only words from the allowed list below (HSK {level} and lower). At most {tolerance} other word(s) per sentence may be outside the list, and only when the sentence would otherwise sound unnatural.
- Only Chinese characters and Chinese punctuation (，。？！、：；“”). Write numbers in Chinese characters (十点, not 10点). No Latin letters, digits or spaces.
- Every sentence of the word must be clearly different from the others, across all senses: vary the situation and the structure.
- Do not write pinyin anywhere.

Translation of each sentence
- Translate directly from the Chinese into natural, everyday target language. It must say exactly what the Chinese says, no more and no less.

Allowed vocabulary (HSK {level} and lower):
{vocab}"""


def translate_system_prompt(language_name: str, style: str) -> str:
    return f"""You translate study content for HanziApp, a Mandarin Chinese course for learners preparing the HSK exam (2025 syllabus). A human editor reviews everything you write before learners see it, so be accurate rather than creative.

{_language_block(language_name, style)}

You receive one HSK word with its senses already fixed: each sense has an id, a grammatical category and Chinese example sentences with ids. Do not change, add or remove senses or sentences. For every sense id write its meaning, and for every sentence id its translation.

{_GLOSS_RULES}

{_MEANING_RULES}

Translation of each sentence
- Translate directly from the Chinese into natural, everyday target language. It must say exactly what the Chinese says, no more and no less. Do not write pinyin or Chinese characters."""


def _glosses_block(glosses) -> str:
    if not glosses:
        return "Reference glosses: none."
    lines = []
    for i, g in enumerate(glosses, start=1):
        kind = "primary" if g.is_primary else "secondary"
        pos = f"[{g.pos_raw}] " if g.pos_raw else ""
        lines.append(f"{i}. {pos}{g.gloss} ({kind})")
    return "Reference glosses (internal, third party — do not copy):\n" + "\n".join(lines)


def _homographs_block(homographs) -> str:
    if not homographs:
        return ""
    lines = [f"- {h.hanzi} ({h.pinyin}, HSK {h.hsk_level}): " + "; ".join(g.gloss for g in h.third_party_glosses.all())
             for h in homographs]
    return "\nOther syllabus entries with the same characters (separate cards, do not cover them here):\n" + "\n".join(lines)


def full_user_message(hanzi: str, syllabus_pinyin: str, level: int, glosses, homographs=()) -> str:
    return (
        f"Word: {hanzi}\nSyllabus pinyin: {syllabus_pinyin}\nHSK level: {level}\n"
        f"{_glosses_block(glosses)}{_homographs_block(homographs)}"
    )


def translate_user_message(hanzi: str, syllabus_pinyin: str, level: int, glosses, senses) -> str:
    lines = []
    for s in senses:
        reading = f", read {s.reading}" if s.reading else ""
        lines.append(f"Sense id {s.pk} [{s.pos or 'unknown'}{reading}]")
        for e in s.examples.all():
            lines.append(f"  Sentence id {e.pk}: {e.text_zh}")
    return (
        f"Word: {hanzi}\nSyllabus pinyin: {syllabus_pinyin}\nHSK level: {level}\n"
        f"{_glosses_block(glosses)}\n\nSenses:\n" + "\n".join(lines)
    )


_EXAMPLE = {
    "type": "object",
    "properties": {
        "zh": {"type": "string", "description": "Chinese sentence (simplified characters)."},
        "translation": {"type": "string", "description": "Translation into the target language."},
    },
    "required": ["zh", "translation"],
    "additionalProperties": False,
}

# Structured Outputs no admite minItems/maxItems > 1: el "exactamente 3" lo
# comprueba la validación sense_count.
FULL_SCHEMA = {
    "type": "object",
    "properties": {
        "senses": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source_gloss": {"type": "integer"},
                    "pos": {"type": "string", "enum": POS_KEYS},
                    "reading": {"type": "string"},
                    "meaning": {"type": "string"},
                    "examples": {"type": "array", "items": _EXAMPLE},
                },
                "required": ["source_gloss", "pos", "reading", "meaning", "examples"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["senses"],
    "additionalProperties": False,
}

TRANSLATE_SCHEMA = {
    "type": "object",
    "properties": {
        "senses": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "sense_id": {"type": "integer"},
                    "meaning": {"type": "string"},
                    "examples": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "sentence_id": {"type": "integer"},
                                "translation": {"type": "string"},
                            },
                            "required": ["sentence_id", "translation"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["sense_id", "meaning", "examples"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["senses"],
    "additionalProperties": False,
}
