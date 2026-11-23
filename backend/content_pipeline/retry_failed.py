"""
retry_failed.py
Reintenta solo las acepciones que fallaron en una corrida anterior de
batch_runner.py (no_text_block, bad_json, needs_regen, errored, expired),
sin volver a gastar en las que ya salieron bien.

Uso:
    # Dry-run:
    python retry_failed.py hsk1_final.json failures.json

    # Envío real, fusionando con los records que ya habían salido bien:
    python retry_failed.py hsk1_final.json failures.json \\
        --previous-records review_queue_raw.json --submit
"""
import json
import argparse

from content_pipeline.batch_runner import build_requests, submit_batch, poll_batch, collect_results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("failures_json")
    parser.add_argument(
        "--previous-records",
        default=None,
        help="JSON de records ya exitosos, para fusionar con los reintentados al final",
    )
    parser.add_argument("--out", default="review_queue_raw_retried.json")
    parser.add_argument("--failures-out", default="failures_retry.json")
    parser.add_argument("--submit", action="store_true")
    args = parser.parse_args()

    with open(args.input_json, encoding="utf-8") as f:
        words = json.load(f)
    words_by_id = {w["no"]: w for w in words}

    with open(args.failures_json, encoding="utf-8") as f:
        failures = json.load(f)

    failed_ids = {f["custom_id"] for f in failures}
    print(f"Acepciones a reintentar: {len(failed_ids)}")

    all_requests = build_requests(words)
    retry_requests = [r for r in all_requests if r["custom_id"] in failed_ids]

    if not args.submit:
        print(f"Dry-run: {len(retry_requests)} requests se reenviarían. Usa --submit para confirmar.")
        return

    import anthropic

    client = anthropic.Anthropic()
    batch = submit_batch(client, retry_requests)
    batch = poll_batch(client, batch.id)
    records, new_failures = collect_results(client, batch.id, words_by_id)

    final_records = list(records)
    if args.previous_records:
        with open(args.previous_records, encoding="utf-8") as f:
            previous = json.load(f)
        final_records = previous + records

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(final_records, f, ensure_ascii=False, indent=2)
    with open(args.failures_out, "w", encoding="utf-8") as f:
        json.dump(new_failures, f, ensure_ascii=False, indent=2)

    print(f"Recuperados: {len(records)} / {len(failed_ids)}")
    print(f"Siguen fallando: {len(new_failures)} -> {args.failures_out}")
    if final_records:
        print(f"Total acumulado: {len(final_records)} -> {args.out}")


if __name__ == "__main__":
    main()
