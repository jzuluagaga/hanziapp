"""
batch_runner.py
Genera requests para el Batch API de Claude usando Structured Outputs (json_schema)
para crear meaning_es y 3 frases de ejemplo naturales por cada acepción del
vocabulario HSK.

Uso:
    export ANTHROPIC_API_KEY="sk-ant-..."

    # Dry-run (no gasta créditos, solo muestra cuántos requests se generarían):
    python batch_runner.py hsk1_final.json

    # Envío real:
    python batch_runner.py hsk1_final.json --submit

    # Si ya tienes un batch corriendo y se cortó el script, retómalo:
    python batch_runner.py hsk1_final.json --batch-id msgbatch_xxx
"""
import json
import argparse
import time

from dotenv import load_dotenv

from content_pipeline.pinyin_gen import a_pinyin

load_dotenv()

MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = """Eres un profesor experto de chino mandarín para hispanohablantes, \
especializado en crear contenido pedagógico de alta calidad para el examen HSK.

Para cada palabra/acepción que te doy, debes generar:
1. Una traducción precisa y natural al español (meaning_es).
2. Exactamente 3 frases de ejemplo en chino que usen esa palabra de forma natural.

Reglas para meaning_es:
- Da SOLO la traducción — una palabra o expresión corta, o varios sinónimos \
separados por punto y coma si hace falta cubrir la acepción.
- NO agregues explicaciones gramaticales ni aclaraciones entre paréntesis \
(por ejemplo, nunca escribas algo como "(verbo copulativo que conecta el \
sujeto con su atributo)"). Nada de notas sobre la función gramatical de la \
palabra — eso ya lo indica el campo aparte de categoría gramatical.

Reglas para las frases de ejemplo:
- Deben sonar naturales y fluidas, como las diría un hablante nativo en un \
contexto cotidiano real. NO restrinjas el vocabulario del resto de la frase a \
una lista cerrada — usa lo que sea necesario para que suene natural.
- Deben ser BREVES: oraciones simples de una sola cláusula, sin conectores \
subordinados innecesarios (evita "y", "porque", "cuando", "que" para unir \
dos ideas en una sola frase). Apunta a frases cortas, apropiadas para un \
estudiante que recién empieza a leer chino.
- La palabra objetivo debe usarse de forma clara e inequívoca en el sentido \
(acepción) indicado, y debe aparecer literalmente en el texto chino de la frase.
- Las 3 frases deben ser claramente distintas entre sí (evita frases casi \
idénticas cambiando solo una palabra).
- Cada frase debe tener su traducción correspondiente al español (sentence_es), \
natural y precisa, traducida DIRECTAMENTE del chino (sentence_zh) — el chino es \
siempre la fuente de verdad.
- No incluyas pinyin en tu respuesta; el pinyin se calcula aparte de forma \
determinista con reglas, no con el modelo.

Sobre la traducción oficial al inglés (translation_en):
Se te da también la traducción oficial al inglés de esta acepción específica, \
tomada del glosario oficial de HSK — una fuente ya verificada por un hablante \
certificado en HSK1 y HSK2. Esa traducción es el ANCLA AUTORITATIVA del \
significado: no la traduzcas palabra por palabra al español, pero meaning_es \
debe expresar exactamente ESE significado de forma natural en español, no uno \
distinto que tú infieras del carácter chino por tu cuenta. El chino sigue \
siendo la fuente de verdad para las frases de ejemplo (cómo se dice, qué suena \
natural), pero si el sentido que te sugiere el carácter chino aislado entra en \
conflicto con lo que indica translation_en, gana translation_en — es la que \
define qué acepción específica te están pidiendo.

Excepción importante: si translation_en describe la FUNCIÓN GRAMATICAL de la \
palabra en vez de su significado semántico (frases del tipo "measure word for \
X", "classifier for X", "prefix for X", "suffix indicating X", "particle \
indicating X"), NO traduzcas esa descripción funcional al español como si \
fuera meaning_es — repetirla violaría la regla de arriba de no agregar \
explicaciones gramaticales, y esa información ya la indica el campo aparte de \
categoría gramatical. En esos casos, meaning_es debe dar el glosario \
semántico de lo que representa X: la cosa que se cuenta o el concepto que \
transmite el sufijo/prefijo/partícula, tal como lo harías para cualquier otra \
palabra. Ejemplo: para translation_en="measure word for small round things" \
(el carácter 点), el meaning_es correcto es algo como "punto; gota" — NUNCA \
"clasificador para cosas pequeñas y redondas".

Sobre sentidos primarios vs. secundarios (is_primary_sense):
Se te indicará también si la acepción que estás generando es un sentido \
PRIMARIO (uso común y cotidiano de la palabra) o SECUNDARIO/marginal (uso \
real pero poco frecuente, más técnico, formal o de registro específico).
- Si es PRIMARIO: genera 3 frases de uso normal, como las diría cualquier \
hablante en el día a día — exactamente como en las reglas de arriba.
- Si es SECUNDARIO/marginal: NO fuerces frases "cotidianas" que no \
corresponden a cómo se usa realmente ese sentido. Es preferible una frase más \
formal, técnica o de registro específico pero honesta sobre su uso real, que \
una frase natural en apariencia pero que ningún hablante diría para expresar \
ese sentido particular. Igual deben seguir siendo frases breves y correctas, \
solo que reflejando el registro real de ese uso.

Responde ÚNICAMENTE en el formato JSON solicitado, sin texto adicional antes ni \
después."""

EXAMPLE_SCHEMA = {
    "type": "object",
    "properties": {
        "zh": {
            "type": "string",
            "description": "Frase de ejemplo en chino (hanzi simplificado)",
        },
        "es": {
            "type": "string",
            "description": "Traducción natural al español de la frase, traducida del chino",
        },
    },
    "required": ["zh", "es"],
    "additionalProperties": False,
}

RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "meaning_es": {
            "type": "string",
            "description": "Traducción precisa y natural al español de esta acepción",
        },
        "examples": {
            "type": "array",
            "items": EXAMPLE_SCHEMA,
            # La API de Structured Outputs de Anthropic solo acepta minItems/
            # maxItems de 0 o 1 para arrays (probado empíricamente: cualquier
            # valor >1 hace fallar el 100% de los requests con
            # "minItems values other than 0 or 1 are not supported"). La
            # garantía de "exactamente 3" sigue siendo responsabilidad de
            # collect_results(), que ya descarta cualquier respuesta con
            # len(examples) != 3.
            "description": "Exactamente 3 frases de ejemplo distintas entre sí",
        },
    },
    "required": ["meaning_es", "examples"],
    "additionalProperties": False,
}


def build_user_prompt(
    hanzi: str, pinyin_ref: str, pos: str, translation_en: str, is_primary: bool
) -> str:
    sense_type = (
        "PRIMARIO (uso común, cotidiano)"
        if is_primary
        else "SECUNDARIO/marginal (uso real pero poco común, registro específico)"
    )
    return (
        f"Palabra: {hanzi}\n"
        f"Pinyin: {pinyin_ref}\n"
        f"Categoría gramatical: {pos or 'N/A'}\n"
        f"Traducción oficial en inglés de esta acepción (glosario HSK, ancla "
        f"autoritativa del significado): {translation_en}\n"
        f"Tipo de sentido: {sense_type}\n\n"
        f"Genera meaning_es y 3 frases de ejemplo según las instrucciones."
    )


def build_requests(words: list[dict]) -> list[dict]:
    """Construye la lista de requests para el Batch API, uno por cada acepción (sense)."""
    requests = []
    for w in words:
        hanzi = w["simplified"]
        pinyin_ref = w.get("pinyin", "")
        for sense in w["senses"]:
            custom_id = f"{w['no']:04d}-{sense['sense_index']}"
            requests.append(
                {
                    "custom_id": custom_id,
                    "params": {
                        "model": MODEL,
                        "max_tokens": 1024,
                        "system": [
                            {
                                "type": "text",
                                "text": SYSTEM_PROMPT,
                                "cache_control": {"type": "ephemeral"},
                            }
                        ],
                        "messages": [
                            {
                                "role": "user",
                                "content": build_user_prompt(
                                    hanzi,
                                    pinyin_ref,
                                    sense.get("pos_raw", ""),
                                    sense.get("translation_en", ""),
                                    sense.get("is_primary", True),
                                ),
                            }
                        ],
                        "output_config": {
                            "format": {
                                "type": "json_schema",
                                "schema": RESULT_SCHEMA,
                            }
                        },
                    },
                }
            )
    return requests


def submit_batch(client, requests: list[dict]):
    batch = client.messages.batches.create(requests=requests)
    print(f"Batch creado: {batch.id} — {len(requests)} requests — status: {batch.processing_status}")
    return batch


def poll_batch(client, batch_id: str, interval: int = 30):
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        print(
            f"[{time.strftime('%H:%M:%S')}] status={batch.processing_status} "
            f"succeeded={batch.request_counts.succeeded} "
            f"errored={batch.request_counts.errored} "
            f"processing={batch.request_counts.processing}"
        )
        if batch.processing_status == "ended":
            return batch
        time.sleep(interval)


def collect_results(client, batch_id: str, words_by_id: dict) -> tuple[list[dict], list[dict]]:
    """Descarga y parsea los resultados del batch. Devuelve (records_ok, failures)."""
    records = []
    failures = []

    for result in client.messages.batches.results(batch_id):
        custom_id = result.custom_id
        word_no_str, sense_idx_str = custom_id.split("-")
        word_no, sense_idx = int(word_no_str), int(sense_idx_str)
        word = words_by_id[word_no]
        sense = word["senses"][sense_idx]

        if result.result.type != "succeeded":
            failures.append(
                {
                    "custom_id": custom_id,
                    "reason": result.result.type,
                    "error": str(getattr(result.result, "error", "")),
                }
            )
            continue

        message = result.result.message
        text_blocks = [b.text for b in message.content if b.type == "text"]

        if not text_blocks:
            failures.append({"custom_id": custom_id, "reason": "no_text_block"})
            continue

        try:
            parsed = json.loads(text_blocks[0])
        except json.JSONDecodeError:
            failures.append(
                {"custom_id": custom_id, "reason": "bad_json", "raw": text_blocks[0][:500]}
            )
            continue

        if len(parsed.get("examples", [])) != 3:
            failures.append(
                {
                    "custom_id": custom_id,
                    "reason": "needs_regen",
                    "detail": f"esperaba 3 ejemplos, recibió {len(parsed.get('examples', []))}",
                }
            )
            continue

        # Post-procesamiento: pinyin determinista para cada frase (nunca del LLM)
        for ex in parsed["examples"]:
            ex["pinyin"] = a_pinyin(ex["zh"])

        records.append(
            {
                "no": word["no"],
                "hanzi": word["simplified"],
                "pinyin": word.get("pinyin", ""),
                "hsk_level": word["hsk_level"],
                "sense_index": sense_idx,
                "pos_raw": sense.get("pos_raw", ""),
                "translation_en": sense.get("translation_en", ""),
                "is_primary_sense": sense.get("is_primary", True),
                "meaning_es": parsed["meaning_es"],
                "examples": parsed["examples"],
            }
        )

    return records, failures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json", help="Ruta al JSON de vocabulario (ej. hsk1_final.json)")
    parser.add_argument("--out", default="review_queue_raw.json", help="Salida con los records generados")
    parser.add_argument("--failures-out", default="failures.json", help="Salida con los fallos")
    parser.add_argument("--submit", action="store_true", help="Envía el batch real (gasta créditos)")
    parser.add_argument("--batch-id", help="ID de un batch ya enviado, para retomar seguimiento")
    args = parser.parse_args()

    with open(args.input_json, encoding="utf-8") as f:
        words = json.load(f)

    words_by_id = {w["no"]: w for w in words}
    requests = build_requests(words)

    n_senses = sum(len(w["senses"]) for w in words)
    print(f"Palabras: {len(words)} — Acepciones (requests): {n_senses}")
    print(f"Modelo: {MODEL}")

    if not args.submit and not args.batch_id:
        print("\nDry-run: no se envió nada. Usa --submit para mandar el batch real.")
        print("Ejemplo de request generado:")
        print(json.dumps(requests[0], ensure_ascii=False, indent=2))
        return

    import anthropic

    client = anthropic.Anthropic()  # lee ANTHROPIC_API_KEY del entorno

    if args.batch_id:
        batch = poll_batch(client, args.batch_id)
    else:
        batch = submit_batch(client, requests)
        batch = poll_batch(client, batch.id)

    records, failures = collect_results(client, batch.id, words_by_id)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    with open(args.failures_out, "w", encoding="utf-8") as f:
        json.dump(failures, f, ensure_ascii=False, indent=2)

    print(f"\nCompletado: {len(records)} OK, {len(failures)} fallos.")
    print(f"Resultados: {args.out}")
    print(f"Fallos (usar con retry_failed.py): {args.failures_out}")


if __name__ == "__main__":
    main()
