"""
Paso 4 de 08-contenido.md §2 (HU-E13-02): genera borradores de base y de
contenido por idioma con la API de Claude.

Por defecto es un ensayo: muestra qué se generaría y un ejemplo de petición,
sin llamar a la API ni gastar créditos.

    # Ensayo
    python manage.py generate_drafts --level 1 --language es
    # Muestra pequeña, sin lote (resultado inmediato)
    python manage.py generate_drafts --level 1 --language es --words 好 只 --sync
    # Nivel completo por lote (50 % más barato; puede tardar)
    python manage.py generate_drafts --level 1 --language es --submit
    # Retomar un lote ya enviado
    python manage.py generate_drafts --collect msgbatch_xxx

Añadir un idioma (08-contenido.md §8) es el mismo comando con --language en:
sobre palabras con base, solo genera significados y traducciones.
"""
import json
import time

from decouple import config
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from content.models import GenerationJob, Word
from content.services.environment import build_environment
from content.services.generation import (
    GenerationError, build_request, collect_batch, run_sync, select_targets, submit_batch,
)
from languages.models import Language


class Command(BaseCommand):
    help = "Genera borradores (base + idioma, o solo idioma) con la API de Claude."

    def add_arguments(self, parser):
        parser.add_argument("--level", type=int, help="Nivel HSK a generar.")
        parser.add_argument("--language", default="es", help="Código del idioma de estudio (por defecto es).")
        parser.add_argument("--words", nargs="*", help="Limitar a estas palabras (hanzi).")
        parser.add_argument("--limit", type=int, help="Limitar a las primeras N palabras pendientes.")
        parser.add_argument("--regenerate", action="store_true",
                            help="Rehace los borradores de ese idioma (y la base si es generada). Nunca toca lo publicado.")
        parser.add_argument("--replace-base-drafts", action="store_true",
                            help="Rehace también bases en borrador importadas o editadas a mano (se pierden esas ediciones).")
        parser.add_argument("--model", default=getattr(settings, "CONTENT_GENERATION_MODEL", "claude-sonnet-5-5"))
        parser.add_argument("--effort", default=getattr(settings, "CONTENT_GENERATION_EFFORT", "medium"),
                            choices=["low", "medium", "high", "xhigh", "max"], help="output_config.effort")
        parser.add_argument("--sync", action="store_true", help="Llama a la API palabra por palabra (para muestras).")
        parser.add_argument("--submit", action="store_true", help="Envía un lote al Batch API y espera el resultado.")
        parser.add_argument("--no-wait", action="store_true", help="Con --submit: no esperar; recoger después con --collect.")
        parser.add_argument("--collect", metavar="BATCH_ID", help="Recoge un lote ya enviado.")

    def _client(self):
        import anthropic

        key = config("ANTHROPIC_API_KEY", default="")
        return anthropic.Anthropic(api_key=key) if key else anthropic.Anthropic()

    def handle(self, *args, **o):
        import anthropic

        try:
            return self._handle(**o)
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as e:
            raise CommandError(
                f"La API rechazó la credencial ({e.status_code}). Revisa ANTHROPIC_API_KEY en .env. "
                "No se guardó nada de la palabra en curso."
            )
        except anthropic.NotFoundError as e:
            raise CommandError(f"Modelo o recurso no encontrado: {e.message}")

    def _handle(self, **o):
        env = build_environment()

        if o["collect"]:
            job = GenerationJob.objects.filter(batch_id=o["collect"]).first()
            if job is None:
                raise CommandError("Ese lote no fue enviado desde aquí (no está en GenerationJob).")
            if job.status == GenerationJob.Status.COLLECTED:
                raise CommandError(f"Ese lote ya se recogió: {job.summary}")
            self._wait_and_collect(self._client(), job, env)
            return

        if not o["level"] and not o["words"]:
            raise CommandError("Indica --level o --words.")
        try:
            language = Language.objects.get(code=o["language"])
        except Language.DoesNotExist:
            raise CommandError(f"El idioma '{o['language']}' no está cargado en la tabla de idiomas.")

        words = Word.objects.filter(retired_at__isnull=True)
        if o["level"]:
            words = words.filter(hsk_level=o["level"])
        if o["words"]:
            words = words.filter(hanzi__in=o["words"])
            missing = set(o["words"]) - set(words.values_list("hanzi", flat=True))
            if missing:
                raise CommandError(f"No están en el sílabo cargado: {', '.join(sorted(missing))}")
        targets, skipped = select_targets(words.order_by("hsk_level", "syllabus_order"), language,
                                          o["regenerate"], o["replace_base_drafts"])
        if o["limit"]:
            targets = targets[: o["limit"]]

        modes = {m: sum(t.mode == m for t in targets) for m in ("full", "translate")}
        self.stdout.write(
            f"Idioma: {language.code} · modelo: {o['model']} ({o['effort']}) · a generar: {len(targets)} "
            f"(base+idioma: {modes['full']}, solo idioma: {modes['translate']}) · omitidas: {len(skipped)}"
        )
        if not targets:
            return
        try:
            sample = build_request(targets[0], language, env, o["model"], o["effort"])
        except GenerationError as e:
            raise CommandError(str(e))

        if o["sync"]:
            summary = run_sync(self._client(), targets, language, env, o["model"], log=self.stdout.write,
                               replace_base_drafts=o["replace_base_drafts"], effort=o["effort"])
            self._report(summary)
        elif o["submit"]:
            try:
                job = submit_batch(self._client(), targets, language, env, o["model"], o["replace_base_drafts"], o["effort"])
            except GenerationError as e:
                raise CommandError(str(e))
            self.stdout.write(self.style.SUCCESS(f"Lote enviado: {job.batch_id}"))
            if o["no_wait"]:
                self.stdout.write(f"Recógelo con: python manage.py generate_drafts --collect {job.batch_id}")
                return
            self._wait_and_collect(self._client(), job, env)
        else:
            self.stdout.write("\nEnsayo: no se llamó a la API. Usa --sync (muestra) o --submit (lote).")
            self.stdout.write(f"Primera petición ({targets[0].word.hanzi}, modo {targets[0].mode}):")
            self.stdout.write(json.dumps({**sample, "system": "[…system prompt…]"}, ensure_ascii=False, indent=2))
            self.stdout.write("\nSystem prompt:\n" + sample["system"][0]["text"][:3000])

    def _wait_and_collect(self, client, job, env):
        while True:
            batch = client.messages.batches.retrieve(job.batch_id)
            c = batch.request_counts
            self.stdout.write(f"[{time.strftime('%H:%M:%S')}] {batch.processing_status} · ok={c.succeeded} "
                              f"error={c.errored} en_proceso={c.processing}")
            if batch.processing_status == "ended":
                break
            time.sleep(30)
        self._report(collect_batch(client, job, env))

    def _report(self, summary):
        self.stdout.write(self.style.SUCCESS(f"Borradores guardados: {summary['stored']}"))
        for f in summary["failures"]:
            self.stdout.write(self.style.WARNING(f"  ✗ {f['custom_id']}: {f['reason']}"))
        if summary["failures"]:
            self.stdout.write("Vuelve a ejecutar el mismo comando para reintentar solo las que fallaron.")
        self.stdout.write("Siguiente paso: revisar en el panel (Contenido › Borradores) y publicar.")
