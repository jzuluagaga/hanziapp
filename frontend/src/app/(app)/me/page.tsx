"use client";

import { BookCheck, Flame, Lock, PenLine, Settings, Sparkles } from "lucide-react";
import Link from "next/link";
import { CurvedPage } from "@/components/layout/curved-header";
import { StreakCard } from "@/components/study/streak-card";
import { Mascot } from "@/components/ui/mascot";
import { ProgressBar, SectionTitle } from "@/components/ui/primitives";
import { Splash } from "@/components/layout/auth-gate";
import { addDays, weekdayIndex } from "@/lib/domain/day";
import { useT } from "@/lib/i18n";
import { loadProgress } from "@/lib/store/actions";
import { useDb } from "@/lib/store/db";
import { canStudyLevel, dayLogOf, profileOf, streakOf } from "@/lib/store/selectors";
import { useLoad } from "@/lib/store/use-load";

export default function MePage() {
  const db = useDb();
  const { t, tp, lang } = useT();
  const profile = profileOf(db);
  useLoad(loadProgress, []);
  if (!db.progress) return <Splash />;
  const progress = db.progress;
  const p = { learnedWords: progress.learned_words, learnedChars: progress.learned_chars, totalAnswers: progress.total_answers, levels: progress.levels };
  const s = streakOf(db);
  const dayLog = dayLogOf(db);
  const since = db.me ? new Intl.DateTimeFormat(lang, { month: "long", year: "numeric" }).format(new Date(db.me.account.created_at)) : "";

  // Calendario de las últimas 6 semanas (lunes a domingo)
  const start = addDays(s.today, -weekdayIndex(s.today) - 35);
  const days = Array.from({ length: 42 }, (_, i) => addDays(start, i));

  const stats = [
    { icon: BookCheck, value: p.learnedWords, label: t("me.stats.learnedWords"), color: "bg-primary" },
    { icon: PenLine, value: p.learnedChars, label: t("me.stats.learnedChars"), color: "bg-success" },
    { icon: Flame, value: tp("common.days", s.max), label: t("me.stats.maxStreak"), color: "bg-amber" },
    { icon: Sparkles, value: p.totalAnswers, label: t("me.stats.answers"), color: "bg-info" },
  ];

  return (
    <CurvedPage
      variant="rays"
      header={
        <div className="relative pb-2 pt-4 text-center">
          <Link href="/me/settings" aria-label={t("a11y.settings")} className="absolute right-0 top-4 grid size-10 place-items-center rounded-full bg-white text-ink shadow-soft">
            <Settings className="size-5" />
          </Link>
          <div className="mx-auto mt-6 grid size-24 place-items-center overflow-hidden rounded-full border-4 border-white bg-peach shadow-soft">
            <Mascot pose="saluda" size={96} className="translate-y-2 scale-125" priority />
          </div>
        </div>
      }
    >
      <div className="-mt-1 text-center">
        <h1 className="text-[26px] font-black leading-tight">{profile.name}</h1>
        <p className="text-sm font-semibold text-ink-2">{t("me.since", { date: since })}</p>
      </div>

      <SectionTitle>{t("me.stats")}</SectionTitle>
      <section className="grid grid-cols-2 gap-x-4 gap-y-5 rounded-[24px] bg-surface p-5">
        {stats.map(({ icon: Icon, value, label, color }) => (
          <div key={label} className="flex items-center gap-3">
            <span className={`grid size-10 shrink-0 place-items-center rounded-xl text-white ${color}`}>
              <Icon className="size-5" aria-hidden />
            </span>
            <span className="min-w-0">
              <span className="block text-lg font-black leading-tight">{value}</span>
              <span className="block text-xs font-semibold leading-tight text-ink-2">{label}</span>
            </span>
          </div>
        ))}
      </section>

      <div className="mt-8">
        <StreakCard />
      </div>

      <SectionTitle>{t("me.calendar")}</SectionTitle>
      <section className="rounded-[24px] bg-card p-5 shadow-soft">
        <div className="grid grid-cols-7 gap-2 text-center">
          {Array.from({ length: 7 }, (_, i) => (
            <span key={i} className="text-[11px] font-bold text-ink-3">
              {t(`weekday.${i}` as "weekday.0")}
            </span>
          ))}
          {days.map((d) => {
            const isToday = d === s.today;
            const st = isToday ? (s.todayActive ? "active" : undefined) : dayLog[d];
            const future = d > s.today;
            return (
              <span
                key={d}
                title={`${d}${st ? ` · ${t(`day.${st}`)}` : ""}`}
                className={`mx-auto size-8 rounded-lg sm:size-9 ${
                  st === "active" ? "bg-amber" : st === "exempt" ? "bg-surface" : st === "missed" ? "bg-error-soft ring-2 ring-inset ring-error/30" : future ? "" : "bg-surface/50"
                } ${isToday ? "ring-2 ring-ink ring-offset-2 ring-offset-card" : ""}`}
              />
            );
          })}
        </div>
        <div className="mt-4 flex flex-wrap justify-center gap-4 text-xs font-bold text-ink-2">
          <span className="flex items-center gap-1.5">
            <span className="size-3 rounded bg-amber" /> {t("day.active")}
          </span>
          <span className="flex items-center gap-1.5">
            <span className="size-3 rounded bg-surface ring-1 ring-border" /> {t("day.exempt")}
          </span>
          <span className="flex items-center gap-1.5">
            <span className="size-3 rounded bg-error-soft ring-1 ring-error/40" /> {t("day.missed")}
          </span>
        </div>
      </section>

      <SectionTitle>{t("me.progress")}</SectionTitle>
      <ul className="space-y-3">
        {p.levels.map((l) => {
          const allowed = canStudyLevel(db, l.level);
          return (
            <li key={l.level} className="rounded-[22px] bg-surface p-4">
              <div className="mb-2 flex items-center justify-between gap-2">
                <span className="flex items-center gap-2 font-extrabold">
                  {t("common.level", { level: l.level })}
                  {!allowed && <Lock className="size-3.5 text-ink-3" aria-label={t("common.locked")} />}
                </span>
                <span className="text-sm font-bold text-ink-2">{t("me.progress.learned", { learned: l.learned, total: l.total })}</span>
              </div>
              <ProgressBar value={l.learned} max={l.total} tone={allowed ? "success" : "info"} />
              <p className="mt-1.5 text-xs font-semibold text-ink-3">{t("me.progress.published", { published: l.published })}</p>
            </li>
          );
        })}
      </ul>
      <p className="mt-3 text-center text-xs font-semibold text-ink-3">{t("me.learnedHint")}</p>
    </CurvedPage>
  );
}
