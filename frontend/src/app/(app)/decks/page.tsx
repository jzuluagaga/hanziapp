"use client";

import { BookOpen, ChevronRight, Lock } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { CurvedPage, levelColor } from "@/components/layout/curved-header";
import { Mascot } from "@/components/ui/mascot";
import { Badge, ProgressBar } from "@/components/ui/primitives";
import { ButtonLink } from "@/components/ui/button";
import { deckLabel } from "@/components/study/skill-meta";
import type { HskLevel } from "@/lib/domain/types";
import { useT } from "@/lib/i18n";
import { loadDecks, loadLevels, loadProgress } from "@/lib/store/actions";
import { useDb } from "@/lib/store/db";
import { useLoad } from "@/lib/store/use-load";

const LEVELS: HskLevel[] = [1, 2, 3, 4, 5, 6];

export default function DecksPage() {
  return (
    <Suspense>
      <Decks />
    </Suspense>
  );
}

function Decks() {
  const db = useDb();
  const { t, tp } = useT();
  const router = useRouter();
  const params = useSearchParams();
  const level = (Number(params.get("level")) || 1) as HskLevel;
  useLoad(() => Promise.all([loadLevels(), loadProgress()]), []);
  useLoad(() => loadDecks(level), [level]);
  const info = db.levels?.find((l) => l.level === level);
  const learned = db.progress?.levels.find((l) => l.level === level)?.learned ?? 0;
  const progress = { total: info?.total ?? 0, published: info?.published ?? 0, learned };
  const allowed = !(info?.locked ?? true);
  const decks = db.decks[level] ?? [];

  return (
    <CurvedPage
      variant="amber"
      header={
        <div className="flex items-end justify-between pt-6">
          <div className="pb-4">
            <h1 className="text-3xl font-black">{t("decks.title")}</h1>
            <p className="mt-1 font-semibold text-white/90">{t("decks.subtitle")}</p>
          </div>
          <Mascot pose="saluda" size={92} className="-mb-8 drop-shadow-lg" />
        </div>
      }
    >
      {/* Selector de nivel */}
      <div role="tablist" aria-label={t("decks.title")} className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4 pb-1 sm:-mx-6 sm:px-6">
        {LEVELS.map((l) => {
          const active = l === level;
          const locked = db.levels?.find((x) => x.level === l)?.locked ?? false;
          return (
            <button
              key={l}
              role="tab"
              aria-selected={active}
              onClick={() => router.replace(`/decks?level=${l}`, { scroll: false })}
              className={`flex shrink-0 items-center gap-1.5 rounded-full px-4 py-2.5 text-sm font-extrabold transition ${active ? "bg-ink text-bg" : "bg-surface text-ink-2 hover:text-ink"}`}
            >
              {locked && <Lock className="size-3.5" aria-hidden />}
              {t("common.level", { level: l })}
            </button>
          );
        })}
      </div>

      {/* Resumen del nivel (R-CON-16, R-PRO-06) */}
      <section className="mt-5 rounded-[24px] bg-card p-5 shadow-soft">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-xl font-black">{t("common.level", { level })}</h2>
          <Badge tone={allowed ? "success" : "amber"}>{allowed ? t("common.plan.free") : <><Lock className="size-3" aria-hidden /> {t("common.plan.pro")}</>}</Badge>
        </div>
        <div className="mt-4">
          <ProgressBar value={progress.learned} max={progress.total} tone={allowed ? "amber" : "info"} label={t("decks.level.learned", { learned: progress.learned, total: progress.total })} />
        </div>
        <div className="mt-2 flex flex-wrap justify-between gap-x-4 text-sm font-semibold text-ink-2">
          <span>{t("decks.level.learned", { learned: progress.learned, total: progress.total })}</span>
          <span>{t("decks.level.published", { published: progress.published, total: progress.total })}</span>
        </div>
      </section>

      {!allowed && (
        <section className="mt-4 flex gap-4 rounded-[24px] bg-peach p-5">
          <div className="min-w-0 flex-1">
            <h3 className="font-extrabold">{t("decks.locked.title", { level })}</h3>
            <p className="mt-1 text-sm leading-relaxed text-ink-2">{t("decks.locked.body")}</p>
            <ButtonLink href="/dictionary" variant="secondary" size="sm" className="mt-3 !bg-card">
              <BookOpen className="size-4" aria-hidden /> {t("decks.locked.dictionary")}
            </ButtonLink>
          </div>
        </section>
      )}

      <ul className="mt-5 space-y-3">
        {decks.map((d) => {
          const c = d.counts.recognition;
          const inReview = d.size - d.published;
          return (
            <li key={d.id}>
              <Link href={`/decks/${d.id}`} className="flex items-center gap-4 rounded-[22px] bg-surface p-3 pr-4 transition hover:brightness-[0.98] active:scale-[0.995]">
                <span className="font-hanzi relative grid size-16 shrink-0 place-items-center overflow-hidden rounded-2xl text-3xl font-bold text-white" style={{ background: levelColor[d.level] }}>
                  <span aria-hidden className="absolute -bottom-5 -right-5 size-12 rounded-full bg-white/20" />
                  {d.locked ? <Lock className="size-6" aria-hidden /> : d.index}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block font-extrabold">{deckLabel(t, { index: d.index, themeKeys: d.theme_keys, part: d.part })}</span>
                  <span className="block text-sm font-semibold text-ink-2">{tp("common.words", d.size)}</span>
                  <span className="mt-1.5 flex flex-wrap gap-1.5">
                    {c.due > 0 && <Badge tone="hard">{t("decks.meta.due", { count: c.due })}</Badge>}
                    {c.new > 0 && <Badge tone="info">{t("decks.meta.new", { count: c.new })}</Badge>}
                    {inReview > 0 && <Badge>{t("decks.meta.inReview", { count: inReview })}</Badge>}
                  </span>
                </span>
                <ChevronRight className="size-5 shrink-0" aria-hidden />
              </Link>
            </li>
          );
        })}
        {!db.decks[level] && <li className="py-6 text-center text-sm font-semibold text-ink-3">{t("common.loading")}</li>}
      </ul>
    </CurvedPage>
  );
}
