import json
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from vocab.models import Example, Meaning, Word
from vocab.pinyin_utils import tonal_to_numbered


class Command(BaseCommand):
    help = (
        "Carga vocabulario HSK desde un JSON con el esquema de "
        "review_queue_raw.json (no, hanzi, pinyin, hsk_level, sense_index, "
        "pos_raw, translation_en, meaning_es, examples[]). Agrupa las "
        "acepciones por 'no' bajo un mismo Word. Idempotente: correrlo dos "
        "veces no duplica datos."
    )

    def add_arguments(self, parser):
        parser.add_argument('json_path', help='Ruta al archivo JSON a cargar')
        parser.add_argument(
            '--dry-run', action='store_true',
            help='No escribe en la base de datos; solo reporta qué se haría.',
        )

    def handle(self, *args, **options):
        path = options['json_path']
        dry_run = options['dry_run']

        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f"No existe el archivo: {path}")
        except json.JSONDecodeError as e:
            raise CommandError(f"JSON inválido en {path}: {e}")

        by_no = defaultdict(list)
        for row in data:
            by_no[row['no']].append(row)

        if dry_run:
            self._dry_run(by_no)
        else:
            with transaction.atomic():
                self._load(by_no)

    # ------------------------------------------------------------------
    def _resolve_pinyin_numbered(self, hanzi, pinyin_tonal):
        numbered = tonal_to_numbered(hanzi, pinyin_tonal)
        if numbered is None:
            self.stderr.write(self.style.WARNING(
                f"  ! No se pudo derivar pinyin_numbered para {hanzi!r} "
                f"({pinyin_tonal!r}); se deja vacío. Revisar manualmente."
            ))
            return ''
        return numbered

    # ------------------------------------------------------------------
    def _dry_run(self, by_no):
        existing_words = {
            w.source_no: w
            for w in Word.objects.filter(source_no__in=list(by_no.keys()))
        }

        words_new = words_upd = 0
        meanings_new = meanings_upd = 0
        examples_new = examples_upd = 0
        align_warnings = 0

        for no, rows in sorted(by_no.items()):
            hanzi = rows[0]['hanzi']
            pinyin_tonal = rows[0]['pinyin']
            existing_word = existing_words.get(no)

            if tonal_to_numbered(hanzi, pinyin_tonal) is None:
                align_warnings += 1

            if existing_word is None:
                words_new += 1
                existing_meanings = {}
            else:
                words_upd += 1
                existing_meanings = {
                    m.sense_index: m
                    for m in Meaning.objects.filter(word=existing_word)
                }

            for row in rows:
                si = row['sense_index']
                existing_meaning = existing_meanings.get(si)
                if existing_meaning is None:
                    meanings_new += 1
                    existing_examples = set()
                else:
                    meanings_upd += 1
                    existing_examples = set(
                        Example.objects.filter(meaning=existing_meaning)
                        .values_list('order', flat=True)
                    )

                for i, _ in enumerate(row['examples']):
                    if i in existing_examples:
                        examples_upd += 1
                    else:
                        examples_new += 1

        self.stdout.write(self.style.SUCCESS('--- DRY RUN (nada escrito en la base de datos) ---'))
        self.stdout.write(f"Words:    {words_new} nuevos, {words_upd} actualizados")
        self.stdout.write(f"Meanings: {meanings_new} nuevos, {meanings_upd} actualizados")
        self.stdout.write(f"Examples: {examples_new} nuevos, {examples_upd} actualizados")
        if align_warnings:
            self.stdout.write(self.style.WARNING(
                f"Advertencias de alineación pinyin_numbered: {align_warnings} "
                f"(ver mensajes arriba; esos Word quedarían con pinyin_numbered vacío)"
            ))
        self.stdout.write(f"Total grupos (palabras) en el JSON: {len(by_no)}")

    # ------------------------------------------------------------------
    def _load(self, by_no):
        words_new = words_upd = 0
        meanings_new = meanings_upd = 0
        examples_new = examples_upd = 0

        for no, rows in sorted(by_no.items()):
            hanzi = rows[0]['hanzi']
            pinyin_tonal = rows[0]['pinyin']
            hsk_level = rows[0]['hsk_level']
            pinyin_numbered = self._resolve_pinyin_numbered(hanzi, pinyin_tonal)

            word, created = Word.objects.update_or_create(
                source_no=no,
                defaults={
                    'hanzi': hanzi,
                    'pinyin_tonal': pinyin_tonal,
                    'pinyin_numbered': pinyin_numbered,
                    'hsk_level': hsk_level,
                },
            )
            words_new += created
            words_upd += not created

            for row in rows:
                meaning, m_created = Meaning.objects.update_or_create(
                    word=word,
                    sense_index=row['sense_index'],
                    defaults={
                        'meaning_es': row['meaning_es'],
                        'pos_raw': row['pos_raw'],
                        'translation_en': row['translation_en'],
                        'validated': True,
                    },
                )
                meanings_new += m_created
                meanings_upd += not m_created

                for i, ex in enumerate(row['examples']):
                    _, e_created = Example.objects.update_or_create(
                        meaning=meaning,
                        order=i,
                        defaults={
                            'sentence_zh': ex['zh'],
                            'sentence_es': ex['es'],
                            'pinyin': ex['pinyin'],
                        },
                    )
                    examples_new += e_created
                    examples_upd += not e_created

        self.stdout.write(self.style.SUCCESS('--- Carga completada ---'))
        self.stdout.write(f"Words:    {words_new} nuevos, {words_upd} actualizados")
        self.stdout.write(f"Meanings: {meanings_new} nuevos, {meanings_upd} actualizados")
        self.stdout.write(f"Examples: {examples_new} nuevos, {examples_upd} actualizados")
