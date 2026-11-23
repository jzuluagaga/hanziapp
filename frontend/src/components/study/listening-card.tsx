"use client";

import { Check, Volume2, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/primitives";
import { play, stopSpeaking } from "@/lib/audio";
import { primaryMeaning } from "@/lib/domain/content";
import type { Grade, LangCode, SessionCard, Word } from "@/lib/domain/types";
import { useT } from "@/lib/i18n";
import { track } from "@/lib/store/actions";
import { useDb } from "@/lib/store/db";

type Extra = { choice: string; replays: number; responseMs: number };

/**
 * HU-E04-02: escucho una palabra y elijo su significado. Las cuatro opciones las fija
 * el servidor (la correcta y tres del mismo nivel) y él decide si fue «Recordé».
 */
export function ListeningCard({ word, card, lang, onAnswer }: { word: Word; card: SessionCard; lang: LangCode; onAnswer: (g: Grade, extra: Extra) => void }) {
  const { t } = useT();
  const db = useDb();
  const [picked, setPicked] = useState<number | null>(null);
  const [playing, setPlaying] = useState(false);
  const replays = useRef(0);
  const shownAt = useRef(0);

  const options = useMemo(() => {
    const ids = card.choices?.length ? card.choices : [word.id];
    return ids.map((id) => ({ id, meaning: (db.words[id] && primaryMeaning(db.words[id], lang)) ?? "—" }));
  }, [card.choices, word.id, db.words, lang]);

  const listen = (auto: boolean) => {
    setPlaying(true);
    if (!auto) replays.current += 1;
    play(word.audio, word.hanzi, () => setPlaying(false))
      .then(() => track("audio_played", { context: "card", target: "word", auto }))
      .catch(() => track("audio_failed", { context: "card", target: "word" }));
    setTimeout(() => setPlaying(false), 2000);
  };

  useEffect(() => {
    shownAt.current = performance.now();
    const id = setTimeout(() => listen(true), 250);
    return () => {
      clearTimeout(id);
      stopSpeaking();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [word.id, card.position]);

  const answered = picked !== null;
  const isRight = answered && options[picked].id === word.id;
  const submit = () => picked !== null && onAnswer(isRight ? "pass" : "fail", { choice: options[picked].id, replays: replays.current, responseMs: performance.now() - shownAt.current });

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!answered && ["1", "2", "3", "4"].includes(e.key)) setPicked(Number(e.key) - 1);
      else if (answered && (e.key === "Enter" || e.key === " ")) {
        e.preventDefault();
        submit();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [answered, isRight, onAnswer, picked]);

  return (
    <div className="flex flex-1 flex-col">
      <div className="animate-pop flex flex-col items-center rounded-[32px] bg-card p-6 shadow-soft">
        <div className="flex w-full gap-1.5">
          <Badge>{t("common.level", { level: word.level })}</Badge>
          {card.reinforcement ? <Badge tone="hard">{t("session.reinforcement")}</Badge> : card.isNew ? <Badge tone="info">{t("session.new")}</Badge> : null}
        </div>
        <button
          type="button"
          onClick={() => listen(false)}
          aria-label={t("session.listen.replay")}
          className={`relative mt-4 grid size-32 place-items-center rounded-full bg-info text-white shadow-[0_8px_0_0_color-mix(in_srgb,var(--info)_70%,black)] transition active:translate-y-1 active:shadow-none`}
        >
          {playing && <span aria-hidden className="absolute inset-0 animate-ping rounded-full bg-info/40" />}
          <Volume2 className="relative size-14" />
        </button>
        <p className="mt-5 text-sm font-bold text-ink-2">{t("session.listen.replay")}</p>

        <div className={`mt-4 min-h-16 text-center transition ${answered ? "opacity-100" : "opacity-0"}`} aria-live="polite">
          {answered && (
            <>
              <p lang="zh-CN" className="font-hanzi text-4xl">{word.hanzi}</p>
              <p className="font-bold text-ink-2">{word.pinyin}</p>
            </>
          )}
        </div>
      </div>

      <p className="mb-3 mt-6 text-center font-extrabold">{t("session.listen.prompt")}</p>
      <div className="grid gap-2.5 sm:grid-cols-2" role="radiogroup" aria-label={t("session.listen.prompt")}>
        {options.map((o, i) => {
          const isCorrect = o.id === word.id;
          const state = !answered ? "idle" : isCorrect ? "right" : i === picked ? "wrong" : "dim";
          return (
            <button
              key={o.id}
              type="button"
              role="radio"
              aria-checked={picked === i}
              disabled={answered}
              onClick={() => setPicked(i)}
              className={`flex min-h-14 items-center gap-3 rounded-2xl border-2 px-4 py-3 text-left text-[15px] font-bold transition ${
                state === "idle"
                  ? "border-border bg-card hover:border-info/50 hover:bg-info-soft"
                  : state === "right"
                    ? "border-success bg-success-soft text-ink"
                    : state === "wrong"
                      ? "border-error bg-error-soft text-ink"
                      : "border-border bg-card opacity-50"
              }`}
            >
              <span className="grid size-7 shrink-0 place-items-center rounded-lg bg-surface text-xs font-black text-ink-2">
                {state === "right" ? <Check className="size-4 text-success" strokeWidth={3} /> : state === "wrong" ? <X className="size-4 text-error" strokeWidth={3} /> : i + 1}
              </span>
              {o.meaning}
            </button>
          );
        })}
      </div>

      <div className="sticky bottom-0 -mx-4 mt-auto bg-gradient-to-t from-bg via-bg to-transparent px-4 pb-[max(1rem,env(safe-area-inset-bottom))] pt-4">
        {answered && (
          <div className="animate-rise">
            <p className={`mb-2 text-center font-extrabold ${isRight ? "text-success" : "text-error"}`}>{isRight ? t("session.listen.correct") : t("session.listen.wrong")}</p>
            <Button block size="lg" variant={isRight ? "success" : "primary"} onClick={submit}>
              {t("common.continue")}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
