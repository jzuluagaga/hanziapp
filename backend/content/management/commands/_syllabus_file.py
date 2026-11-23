"""Lectura de archivos de sílabo. Admite el formato de hsk1_final.json y uno genérico."""
import json

from django.core.management.base import CommandError


def read_syllabus_file(path: str) -> list[dict]:
    """
    Devuelve [{hsk_level, order, hanzi, pinyin, glosses: [{position, pos_raw, gloss, is_primary}]}].

    Campos aceptados por entrada: `hsk_level`; `order` o `no`; `hanzi` o
    `simplified`; `pinyin_pdf` (preferido: es el pinyin del documento oficial) o
    `pinyin`; y opcionalmente `senses` con `translation_en`, `pos_raw`,
    `is_primary`, `sense_index` (glosas de terceros).
    """
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        raise CommandError(f"No existe el archivo: {path}")
    except json.JSONDecodeError as e:
        raise CommandError(f"JSON inválido en {path}: {e}")

    entries = []
    for i, row in enumerate(raw):
        try:
            entry = {
                "hsk_level": int(row["hsk_level"]),
                "order": int(row.get("order", row.get("no"))),
                "hanzi": (row.get("hanzi") or row["simplified"]).strip(),
                "pinyin": (row.get("pinyin_pdf") or row["pinyin"]).strip(),
            }
        except (KeyError, TypeError, ValueError) as e:
            raise CommandError(f"Entrada {i} incompleta ({e}): {row}")
        entry["glosses"] = [
            {
                "position": int(s.get("sense_index", j)),
                "pos_raw": (s.get("pos_raw") or "").strip(),
                "gloss": s["translation_en"].strip(),
                "is_primary": bool(s.get("is_primary", True)),
            }
            for j, s in enumerate(row.get("senses", []))
            if (s.get("translation_en") or "").strip()
        ]
        entries.append(entry)
    return entries
