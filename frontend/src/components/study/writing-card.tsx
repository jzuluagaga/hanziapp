"use client";

import { CheckCircle2, Lightbulb, RotateCcw, XCircle } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import type HanziWriter from "hanzi-writer";
import { AudioButton } from "@/components/word/audio-button";
import { CharGrid } from "@/components/word/char-grid";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/primitives";
import { config } from "@/lib/config";
import { primaryMeaning } from "@/lib/domain/content";
import type { Grade, LangCode, SessionCard, Word } from "@/lib/domain/types";
import { useT } from "@/lib/i18n";
import { track } from "@/lib/store/actions";

type Phase = "guided" | "guided_done" | "recall" | "result";

/**
 * Escritura por carácter (R-ESC-01). Un carácter nuevo se presenta primero con guía,
 * sin calificación, y enseguida de memoria (R-ESC-06). La calificación de memoria la
 * decide el sistema (R-ESC-03).
 */
export function WritingCard({
  word,
  card,
  lang,
  onAnswer,
  onGuided,
}: {
  word: Word;
  card: SessionCard;
  lang: LangCode;
  onAnswer: (g: Grade, extra: { strokeMisses: number; usedHint: boolean }) => void;
  onGuided?: (strokeMisses: number) => void;
}) {
  const { t } = useT();
  const char = card.unit;
  const [phase, setPhase] = useState<Phase>(card.isNew && !card.reinforcement ? "guided" : "recall");
  const [misses, setMisses] = useState(0);
  const [usedHint, setUsedHint] = useState(false);
  const [loadError, setLoadError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const host = useRef<HTMLDivElement>(null);
  const writer = useRef<HanziWriter | null>(null);
  const strokeNum = useRef(0);
  const hintRef = useRef(false);
  const [size, setSize] = useState(280);
  const phaseRef = useRef(phase);
  phaseRef.current = phase;

  // R-ESC-07: salir a mitad de un carácter no guarda nada; solo se registra el abandono.
  useEffect(
    () => () => {
      if (phaseRef.current === "guided" || phaseRef.current === "recall") {
        track("writing_char_abandoned", { strokes_done: strokeNum.current, mode: phaseRef.current });
      }
    },
    [],
  );

  useEffect(() => {
    const fit = () => setSize(Math.min(300, window.innerWidth - 72));
    fit();
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, []);

  const mode = phase === "guided" || phase === "guided_done" ? "guided" : "recall";
  const passed = !usedHint && misses <= config.writingMaxStrokeMisses;

  useEffect(() => {
    if (phase === "guided_done" || phase === "result") return;
    let cancelled = false;
    const el = host.current;
    if (!el) return;
    strokeNum.current = 0;
    import("hanzi-writer").then(({ default: HW }) => {
      if (cancelled) return;
      el.innerHTML = "";
      const css = getComputedStyle(document.documentElement);
      const ink = css.getPropertyValue("--ink").trim() || "#2D2A26";
      const w = HW.create(el, char, {
        width: size,
        height: size,
        padding: 14,
        showCharacter: false,
        showOutline: mode === "guided",
        strokeColor: ink,
        drawingColor: ink,
        drawingWidth: 18,
        outlineColor: css.getPropertyValue("--border").trim() || "#E6E0D6",
        highlightColor: "#4A90E2",
        highlightCompleteColor: mode === "guided" ? "#2A9D8F" : null,
        onLoadCharDataError: () => !cancelled && setLoadError(true),
      });
      writer.current = w;
      w.quiz({
        showHintAfterMisses: config.autoHintAfterMisses,
        onCorrectStroke: (d) => {
          strokeNum.current = d.strokeNum + 1;
        },
        onMistake: (d) => {
          if (mode !== "recall") return;
          setMisses(d.totalMistakes);
          // R-ESC-05: la pista automática tras N errados seguidos cuenta como pista.
          if (d.mistakesOnStroke >= config.autoHintAfterMisses) {
            if (d.mistakesOnStroke === config.autoHintAfterMisses) track("writing_hint_shown", { auto: true });
            hintRef.current = true;
            setUsedHint(true);
          }
        },
        onComplete: (s) => {
          if (cancelled) return;
          if (mode === "guided") {
            onGuided?.(s.totalMistakes);
            setPhase("guided_done");
          }
          else {
            setMisses(s.totalMistakes);
            setPhase("result");
          }
        },
      });
    });
    return () => {
      cancelled = true;
      writer.current?.cancelQuiz();
      writer.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [char, mode, size, attempt, phase]);

  const giveHint = useCallback(() => {
    writer.current?.highlightStroke(strokeNum.current);
    track("writing_hint_shown", { auto: false });
    hintRef.current = true;
    setUsedHint(true);
  }, []);

  const finish = () => onAnswer(passed ? "pass" : "fail", { strokeMisses: misses, usedHint: hintRef.current });

  const meaning = primaryMeaning(word, lang);
  const context = Array.from(word.hanzi).map((c, i) => (
    <span key={i} className={c === char ? "mx-0.5 inline-block rounded-lg border-2 border-dashed border-primary bg-peach px-0.5 text-transparent" : ""}>
      {c}
    </span>
  ));

  return (
    <div className="flex flex-1 flex-col">
      <div className="animate-pop rounded-[32px] bg-card p-5 shadow-soft">
        <div className="flex items-center justify-between gap-2">
          <div className="flex gap-1.5">
            <Badge tone={mode === "guided" ? "success" : "primary"}>{mode === "guided" ? t("session.write.guided") : t("session.write.recall")}</Badge>
            {card.reinforcement && <Badge tone="hard">{t("session.reinforcement")}</Badge>}
            {card.isNew && !card.reinforcement && <Badge tone="info">{t("session.new")}</Badge>}
          </div>
          {word.hasAudio && <AudioButton src={word.audio} text={word.hanzi} size="sm" />}
        </div>

        <div className="mt-3 text-center">
          <p className="text-xs font-extrabold uppercase tracking-wider text-ink-3">{t("session.write.context")}</p>
          <p lang="zh-CN" className="font-hanzi mt-1 text-3xl">
            {mode === "guided" || phase === "result" ? word.hanzi : context}
          </p>
          <p className="font-bold text-ink-2">
            {word.pinyin} · <span className="font-semibold">{meaning}</span>
          </p>
        </div>

        <div className="mx-auto mt-4 grid place-items-center">
          <div className="relative rounded-3xl bg-bg" style={{ width: size, height: size }}>
            <CharGrid />
            {phase === "guided_done" || phase === "result" ? (
              <p lang="zh-CN" className="font-hanzi absolute inset-0 grid place-items-center text-[200px] leading-none" style={{ fontSize: size * 0.72, color: phase === "result" ? (passed ? "var(--success)" : "var(--error)") : "var(--success)" }}>
                {char}
              </p>
            ) : (
              <div ref={host} className="relative touch-none" aria-label={char} />
            )}
          </div>
        </div>

        {loadError && (
          <div className="mt-4 rounded-2xl bg-error-soft p-3 text-center text-sm font-semibold text-error">
            {t("session.write.loadError")}
            <button
              type="button"
              className="ml-2 inline-flex items-center gap-1 underline"
              onClick={() => {
                setLoadError(false);
                setAttempt((a) => a + 1);
              }}
            >
              <RotateCcw className="size-3.5" aria-hidden />
            </button>
          </div>
        )}

        <p className="mt-4 text-center text-sm text-ink-2">{mode === "guided" ? t("session.write.guidedHint") : t("session.write.recallHint")}</p>
        {mode === "recall" && phase === "recall" && (
          <div className="mt-3 flex items-center justify-between">
            <span className="text-sm font-bold text-ink-2">{t("session.write.misses", { count: misses })}</span>
            <Button variant="outline" size="sm" onClick={giveHint}>
              <Lightbulb className="size-4" aria-hidden /> {t("session.write.hint")}
            </Button>
          </div>
        )}
        {usedHint && phase === "recall" && <p className="mt-2 rounded-xl bg-hard-soft p-2.5 text-center text-xs font-bold text-ink-2">{t("session.write.hintWarning")}</p>}
      </div>

      <div className="sticky bottom-0 -mx-4 mt-auto bg-gradient-to-t from-bg via-bg to-transparent px-4 pb-[max(1rem,env(safe-area-inset-bottom))] pt-4">
        {phase === "guided_done" && (
          <div className="animate-rise">
            <p className="mb-2 text-center font-extrabold text-success">{t("session.write.guidedDone")}</p>
            <Button
              block
              size="lg"
              onClick={() => {
                setMisses(0);
                setUsedHint(false);
                hintRef.current = false;
                setPhase("recall");
              }}
            >
              {t("session.write.toRecall")}
            </Button>
          </div>
        )}
        {phase === "result" && (
          <div className="animate-rise">
            <p className={`mb-2 flex items-center justify-center gap-2 font-extrabold ${passed ? "text-success" : "text-error"}`}>
              {passed ? <CheckCircle2 className="size-5" aria-hidden /> : <XCircle className="size-5" aria-hidden />}
              {passed
                ? `${t("session.write.resultPass")} · ${t("session.write.misses", { count: misses })}`
                : usedHint
                  ? t("session.write.resultFailHint")
                  : t("session.write.resultFailMisses", { max: config.writingMaxStrokeMisses })}
            </p>
            <Button block size="lg" variant={passed ? "success" : "primary"} onClick={finish}>
              {t("common.continue")}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
