"use client";

import { Flag, Hourglass } from "lucide-react";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { Splash } from "@/components/layout/auth-gate";
import { Button } from "@/components/ui/button";
import { Badge, Container, SectionTitle, TopBar } from "@/components/ui/primitives";
import { AudioButton } from "@/components/word/audio-button";
import { ReportSheet } from "@/components/word/report-sheet";
import { StrokeAnimation } from "@/components/word/stroke-animation";
import { charactersOf, publishedContent } from "@/lib/domain/content";
import { useT } from "@/lib/i18n";
import { loadWord } from "@/lib/store/actions";
import { useDb } from "@/lib/store/db";
import { profileOf } from "@/lib/store/selectors";

/** HU-E07-02: ficha de la palabra. R-CON-08: publicada → todo; no publicada → solo dato del sílabo. */
export default function WordPage() {
  return (
    <Suspense fallback={<Splash />}>
      <WordView />
    </Suspense>
  );
}

function WordView() {
  const { wordId } = useParams<{ wordId: string }>();
  const from = useSearchParams().get("from");
  const db = useDb();
  const { t } = useT();
  const [report, setReport] = useState(false);
  const [state, setState] = useState<"loading" | "ready" | "missing">("loading");
  useEffect(() => {
    loadWord(wordId, from === "search" || from === "deck" || from === "card" ? from : undefined).then((w) => setState(w ? "ready" : "missing"));
  }, [wordId, from]);
  const word = db.words[wordId];
  const lang = profileOf(db).studyLanguage;

  if (state === "loading" && !word) return <Splash />;
  if (!word) {
    return (
      <>
        <TopBar />
        <Container className="py-16 text-center font-bold">{t("word.notFound")}</Container>
      </>
    );
  }
  const content = publishedContent(word, lang);

  return (
    <div className="pb-28">
      <TopBar
        right={
          <button type="button" onClick={() => setReport(true)} aria-label={t("report.title")} className="grid size-10 place-items-center rounded-full text-ink-2 hover:bg-surface">
            <Flag className="size-5" />
          </button>
        }
      />
      <Container>
        <section className="animate-rise relative overflow-hidden rounded-[32px] bg-card p-6 text-center shadow-soft">
          <div aria-hidden className="absolute -right-10 -top-10 size-40 rounded-full bg-peach" />
          <div aria-hidden className="absolute -bottom-12 -left-8 size-32 rounded-full bg-surface" />
          <div className="relative">
            <div className="flex justify-center gap-1.5">
              <Badge>{t("common.level", { level: word.level })}</Badge>
              <Badge tone="neutral">{t("word.syllabusOrder", { order: word.order })}</Badge>
            </div>
            <p lang="zh-CN" className="font-hanzi mt-4 text-[96px] leading-none">{word.hanzi}</p>
            <div className="mt-4 flex items-center justify-center gap-3">
              <p className="text-2xl font-bold text-ink-2">{word.pinyin}</p>
              {content && word.hasAudio && <AudioButton src={word.audio} text={word.hanzi} context="word_page" />}
            </div>
            {content && <p className="mt-2 text-lg font-extrabold">{content.meanings.join(" · ")}</p>}
          </div>
        </section>

        {!content ? (
          <section className="mt-5 flex gap-3 rounded-[22px] bg-hard-soft p-5">
            <Hourglass className="mt-0.5 size-5 shrink-0 text-hard" aria-hidden />
            <div>
              <p className="font-extrabold">{t("word.inReview.title")}</p>
              <p className="mt-1 text-sm leading-relaxed text-ink-2">{t("word.inReview.body")}</p>
            </div>
          </section>
        ) : (
          <>
            <SectionTitle>{t("word.senses")}</SectionTitle>
            <ol className="space-y-2">
              {word.base.senses.map((s, i) => (
                <li key={i} className="flex items-baseline gap-3 rounded-2xl bg-surface px-4 py-3">
                  <span className="grid size-6 shrink-0 place-items-center rounded-full bg-card text-xs font-black text-ink-2">{i + 1}</span>
                  <span className="min-w-0">
                    <span className="block text-xs font-bold italic text-ink-3">{t(`pos.${s.pos}`)}</span>
                    <span className="block text-[17px] font-bold">{content.meanings[i]}</span>
                  </span>
                </li>
              ))}
            </ol>

            <SectionTitle>{t("word.examples")}</SectionTitle>
            <ul className="space-y-2">
              {word.base.examples.map((ex, i) => (
                <li key={i} className="flex items-start gap-3 rounded-2xl bg-info-soft p-4">
                  <div className="min-w-0 flex-1">
                    <p lang="zh-CN" className="font-hanzi text-xl">{ex.zh}</p>
                    <p className="text-sm text-ink-2">{ex.pinyin}</p>
                    <p className="mt-1 text-[15px]">{content.translations[i]}</p>
                  </div>
                  {ex.audio ? <AudioButton src={ex.audio} text={ex.zh} context="word_page" target="example" size="sm" /> : <span className="text-xs font-bold text-ink-3">{t("word.noAudio")}</span>}
                </li>
              ))}
            </ul>

            <SectionTitle>{t("word.strokes")}</SectionTitle>
            <div className="flex flex-wrap justify-center gap-4 rounded-[22px] bg-surface p-4">
              {charactersOf(word).map((c) => (
                  <StrokeAnimation key={c} char={c} />
                ))}
            </div>
          </>
        )}

        <Button variant="ghost" block className="mt-8" onClick={() => setReport(true)}>
          <Flag className="size-4" aria-hidden /> {t("report.title")}
        </Button>
      </Container>
      <ReportSheet word={word} open={report} onClose={() => setReport(false)} />
    </div>
  );
}
