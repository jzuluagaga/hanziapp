"use client";

import { Flag } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { AudioButton } from "@/components/word/audio-button";
import { ReportSheet } from "@/components/word/report-sheet";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/primitives";
import { publishedContent } from "@/lib/domain/content";
import type { Grade, LangCode, SessionCard, Word } from "@/lib/domain/types";
import { useT } from "@/lib/i18n";

/**
 * HU-E03-02: veo el hanzi, revelo pinyin y significado, y digo si recordé.
 * Solo dos calificaciones: Recordé / No recordé (R-REP-03, D-42).
 */
export function RecognitionCard({ word, card, lang, onAnswer }: { word: Word; card: SessionCard; lang: LangCode; onAnswer: (g: Grade) => void }) {
  const { t } = useT();
  const [revealed, setRevealed] = useState(false);
  const [report, setReport] = useState(false);
  const content = publishedContent(word, lang);

  const answer = useCallback((g: Grade) => revealed && onAnswer(g), [revealed, onAnswer]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (report || e.target instanceof HTMLTextAreaElement || e.target instanceof HTMLInputElement) return;
      if (!revealed && (e.key === " " || e.key === "Enter")) {
        e.preventDefault();
        setRevealed(true);
      } else if (revealed && e.key === "1") answer("fail");
      else if (revealed && e.key === "2") answer("pass");
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [revealed, answer, report]);

  return (
    <div className="flex flex-1 flex-col">
      <div className="animate-pop relative flex flex-1 flex-col rounded-[32px] bg-card p-6 shadow-soft">
        <div className="flex items-center justify-between gap-2">
          <div className="flex gap-1.5">
            <Badge>{t("common.level", { level: word.level })}</Badge>
            {card.reinforcement ? <Badge tone="hard">{t("session.reinforcement")}</Badge> : card.isNew ? <Badge tone="info">{t("session.new")}</Badge> : null}
          </div>
          <button type="button" onClick={() => setReport(true)} aria-label={t("session.report")} className="grid size-9 place-items-center rounded-full text-ink-3 hover:bg-surface hover:text-ink-2">
            <Flag className="size-4" />
          </button>
        </div>

        <div className="flex flex-1 flex-col justify-center">
        <div className={`flex flex-col items-center justify-center text-center transition-all ${revealed ? "py-4" : "py-10"}`}>
          <p lang="zh-CN" className={`font-hanzi font-medium leading-none text-ink transition-all ${revealed ? "text-6xl" : "text-[88px] sm:text-[104px]"}`}>
            {word.hanzi}
          </p>
        </div>

        {revealed && content && (
          <div className="animate-rise space-y-5">
            <div className="flex items-center justify-center gap-3">
              <p className="text-2xl font-bold text-ink-2">{word.pinyin}</p>
              {word.hasAudio && <AudioButton src={word.audio} text={word.hanzi} />}
            </div>
            <div>
              <p className="mb-2 text-xs font-extrabold uppercase tracking-wider text-ink-3">{t("session.meanings")}</p>
              <ol className="space-y-1.5">
                {word.base.senses.map((s, i) => (
                  <li key={i} className="flex items-baseline gap-2 text-lg font-bold">
                    <span className="text-sm font-semibold italic text-ink-3">{t(`pos.${s.pos}`)}</span>
                    <span>{content.meanings[i]}</span>
                  </li>
                ))}
              </ol>
            </div>
            {word.base.examples[0] && (
              <div className="rounded-2xl bg-surface p-4">
                <div className="flex items-start gap-3">
                  <div className="min-w-0 flex-1">
                    <p lang="zh-CN" className="font-hanzi text-lg">{word.base.examples[0].zh}</p>
                    <p className="text-sm text-ink-2">{word.base.examples[0].pinyin}</p>
                    <p className="mt-1 text-[15px]">{content.translations[0]}</p>
                  </div>
                  {word.base.examples[0].audio && <AudioButton src={word.base.examples[0].audio} text={word.base.examples[0].zh} target="example" size="sm" />}
                </div>
              </div>
            )}
          </div>
        )}
        </div>
      </div>

      <div className="sticky bottom-0 -mx-4 mt-4 bg-gradient-to-t from-bg via-bg to-transparent px-4 pb-[max(1rem,env(safe-area-inset-bottom))] pt-3">
        {!revealed ? (
          <Button block size="lg" onClick={() => setRevealed(true)}>
            {t("session.show")}
          </Button>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            <Button size="lg" variant="fail" onClick={() => answer("fail")}>
              {t("session.fail")}
            </Button>
            <Button size="lg" variant="success" onClick={() => answer("pass")}>
              {t("session.pass")}
            </Button>
          </div>
        )}
        <p className="mt-2 hidden text-center text-xs text-ink-3 sm:block">{t("session.shortcuts")}</p>
      </div>
      <ReportSheet word={word} open={report} onClose={() => setReport(false)} />
    </div>
  );
}
