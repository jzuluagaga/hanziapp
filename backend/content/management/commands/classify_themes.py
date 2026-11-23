"""
Propone el subtema de cada palabra (D-49, 08-contenido.md §7) con la API de Claude.
Las propuestas quedan como borrador hasta que el editor las aprueba en el panel.

Por defecto es un ensayo: cuenta peticiones y tokens de entrada (sin gastar créditos)
y estima el costo.

    python manage.py classify_themes --level 1 --level 2              # ensayo
    python manage.py classify_themes --sample 100 --sync               # muestra con resultado inmediato
    python manage.py classify_themes --level 1 --level 2 --submit      # lote (mitad de precio)
    python manage.py classify_themes --collect msgbatch_xxx            # recoger un lote
"""
import time

from decouple import config
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from content.models import GenerationJob
from content.services import themes

# Precio de referencia por millón de tokens (Sonnet 5.5, noviembre de 2026); el lote cuesta la mitad.
PRICE_IN, PRICE_OUT = 2.0, 10.0


class Command(BaseCommand):
    help = "Propone el subtema de cada palabra con la API de Claude (D-49)."

    def add_arguments(self, parser):
        parser.add_argument("--level", type=int, action="append")
        parser.add_argument("--words", nargs="*", help="Solo estas palabras (hanzi).")
        parser.add_argument("--sample", type=int, help="Muestra al azar repartida entre niveles.")
        parser.add_argument("--regenerate", action="store_true", help="Rehace borradores (nunca lo aprobado).")
        parser.add_argument("--model", default=getattr(settings, "CONTENT_GENERATION_MODEL", "claude-sonnet-5-5"))
        parser.add_argument("--effort", default="low", choices=["low", "medium", "high", "xhigh", "max"])
        parser.add_argument("--sync", action="store_true")
        parser.add_argument("--submit", action="store_true")
        parser.add_argument("--no-wait", action="store_true")
        parser.add_argument("--collect", metavar="BATCH_ID")

    def _client(self):
        import anthropic

        key = config("ANTHROPIC_API_KEY", default="")
        return anthropic.Anthropic(api_key=key) if key else anthropic.Anthropic()

    def _report(self, summary):
        self.stdout.write(f"Guardadas: {summary['stored']}")
        for p in summary["problems"][:30]:
            self.stdout.write(self.style.WARNING(f"  {p}"))
        u = summary.get("usage") or {}
        if u:
            cost = (u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) * 1.25
                    + u.get("cache_read_input_tokens", 0) * 0.1) * PRICE_IN / 1e6 + u.get("output_tokens", 0) * PRICE_OUT / 1e6
            self.stdout.write(f"Tokens: {u}  ·  costo aproximado sin descuento de lote: {cost:.4f} USD")

    def handle(self, *args, level=None, words=None, sample=None, regenerate=False, model=None, effort=None,
               sync=False, submit=False, no_wait=False, collect=None, **opts):
        if collect:
            job = GenerationJob.objects.filter(batch_id=collect, kind="themes").first()
            if job is None:
                raise CommandError("Lote desconocido.")
            client = self._client()
            if client.messages.batches.retrieve(collect).processing_status != "ended":
                self.stdout.write("El lote aún no termina.")
                return
            self._report(themes.collect_batch(client, job))
            return

        selected = themes.select_words(level, words, regenerate, sample)
        groups = themes.chunks(selected)
        self.stdout.write(f"{len(selected)} palabras en {len(groups)} peticiones (modelo {model}, esfuerzo {effort}).")
        if not selected:
            return
        if sync:
            self._report(themes.run_sync(self._client(), selected, model, effort, log=self.stdout.write))
            return
        if submit:
            client = self._client()
            job = themes.submit_batch(client, selected, model, effort)
            self.stdout.write(f"Lote enviado: {job.batch_id}")
            if no_wait:
                return
            while client.messages.batches.retrieve(job.batch_id).processing_status != "ended":
                time.sleep(30)
            self._report(themes.collect_batch(client, job))
            return

        # Ensayo: tokens de entrada contados por la API (gratis); la salida se estima.
        client = self._client()
        tokens_in = 0
        for g in groups:
            req = themes.build_request(g, model, effort)
            tokens_in += client.messages.count_tokens(model=model, system=req["system"], messages=req["messages"]).input_tokens
        tokens_out = len(selected) * 15 + len(groups) * 2000  # respuesta + razonamiento estimado
        cost = tokens_in * PRICE_IN / 1e6 + tokens_out * PRICE_OUT / 1e6
        self.stdout.write(f"Entrada contada: {tokens_in} tokens · salida estimada: {tokens_out} tokens")
        self.stdout.write(f"Costo estimado: {cost:.2f} USD en modo síncrono, {cost / 2:.2f} USD por lote.")
        self.stdout.write("Nada se envió. Usa --sync (muestras) o --submit (lote) para clasificar.")
