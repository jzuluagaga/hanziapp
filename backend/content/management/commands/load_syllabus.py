"""
Paso 1 de 08-contenido.md §2 (HU-E13-01): carga las palabras de un nivel con
sus datos del sílabo y su orden. Repetirlo no duplica nada.

- La identidad de una palabra es su posición en el sílabo (nivel + número de
  orden). Corregir el hanzi o el pinyin conserva su id (R-CON-03).
- Con `--gloss-source`, carga además las glosas de terceros del archivo como
  campo interno con su fuente (R-CON-02). Nunca se muestran.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from content.models import ThirdPartyGloss, Word
from ops.services import audit

from ._syllabus_file import read_syllabus_file


class Command(BaseCommand):
    help = "Carga o actualiza palabras del sílabo (y, opcionalmente, glosas de terceros internas)."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Archivo JSON del sílabo, p. ej. content_pipeline/hsk1_final.json")
        parser.add_argument("--gloss-source", default="",
                            help="Nombre de la fuente de las glosas del archivo (p. ej. mandarin_bean). Sin él no se cargan glosas.")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, path, gloss_source, dry_run, **opts):
        entries = read_syllabus_file(path)
        created = updated = unchanged = glosses = 0
        with transaction.atomic():
            for e in entries:
                word = Word.objects.filter(hsk_level=e["hsk_level"], syllabus_order=e["order"]).first()
                if word is None:
                    created += 1
                    if not dry_run:
                        word = Word.objects.create(
                            hsk_level=e["hsk_level"], syllabus_order=e["order"], hanzi=e["hanzi"], pinyin=e["pinyin"],
                        )
                elif (word.hanzi, word.pinyin) != (e["hanzi"], e["pinyin"]):
                    updated += 1
                    self.stdout.write(f"  corrige #{e['order']}: {word.hanzi} {word.pinyin} → {e['hanzi']} {e['pinyin']}")
                    if not dry_run:
                        old = {"hanzi": word.hanzi, "pinyin": word.pinyin}
                        word.hanzi, word.pinyin = e["hanzi"], e["pinyin"]
                        word.save(update_fields=["hanzi", "pinyin", "updated_at"])
                        audit(None, "syllabus_corrected", word, "load_syllabus", old=old,
                              new={"hanzi": word.hanzi, "pinyin": word.pinyin})
                else:
                    unchanged += 1
                if gloss_source and e["glosses"] and not dry_run:
                    for g in e["glosses"]:
                        _, made = ThirdPartyGloss.objects.update_or_create(
                            word=word, source=gloss_source, position=g["position"],
                            defaults={"pos_raw": g["pos_raw"], "gloss": g["gloss"], "is_primary": g["is_primary"]},
                        )
                        glosses += made
            if dry_run:
                transaction.set_rollback(True)

        prefix = "[dry-run] " if dry_run else ""
        self.stdout.write(self.style.SUCCESS(
            f"{prefix}Palabras: {created} nuevas, {updated} corregidas, {unchanged} sin cambios. "
            f"Glosas nuevas: {glosses}."
        ))
        if not gloss_source and any(e["glosses"] for e in entries):
            self.stdout.write("El archivo trae glosas; usa --gloss-source <fuente> para cargarlas como campo interno.")
