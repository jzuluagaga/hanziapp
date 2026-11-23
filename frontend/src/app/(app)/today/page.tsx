"use client";

import { ChevronRight, Lightbulb, Play, RotateCcw } from "lucide-react";
import Link from "next/link";
import { CurvedPage, levelColor } from "@/components/layout/curved-header";
import { SKILLS, SkillIcon, scopeLabel, skillTone, studyHref } from "@/components/study/skill-meta";
import { StreakCard } from "@/components/study/streak-card";
import { ButtonLink } from "@/components/ui/button";
import { Mascot } from "@/components/ui/mascot";
import { ProgressBar, SectionTitle } from "@/components/ui/primitives";
import { useToast } from "@/components/ui/toast";
import { Splash } from "@/components/layout/auth-gate";
import { hourIn } from "@/lib/domain/day";
import { useT } from "@/lib/i18n";
import { discardSession, loadToday } from "@/lib/store/actions";
import { useDb } from "@/lib/store/db";
import { latestActiveSession, profileOf } from "@/lib/store/selectors";
import { useLoad } from "@/lib/store/use-load";

export default function TodayPage() {
  const db = useDb();
  const { t, tp } = useT();
  const toast = useToast();
  const profile = profileOf(db);
  useLoad(loadToday, []);
  if (!db.today) return <Splash />;
  const counts = SKILLS.map((skill) => ({ skill, due: db.today!.counts[skill].due, fresh: db.today!.counts[skill].new }));
  const totalDue = counts.reduce((n, c) => n + c.due, 0);
  const totalNew = counts.reduce((n, c) => n + c.fresh, 0);
  const resume = latestActiveSession(db);

  const hour = hourIn(profile.timezone);
  const greetingKey = hour >= 4 && hour < 12 ? "greeting.morning" : hour >= 12 && hour < 19 ? "greeting.afternoon" : "greeting.evening";
  const firstName = profile.name.split(" ")[0];

  // R-SES-12: "Estudiar hoy" empieza por la primera habilidad con algo que hacer.
  const firstSkill = counts.find((c) => c.due + c.fresh > 0)?.skill;

  return (
    <CurvedPage
      variant="sunrise"
      clouds
      header={
        <div className="flex items-end justify-between gap-2 pt-6">
          <div className="min-w-0 pb-8">
            <p className="text-sm font-bold text-white/85">{t("app.name")}</p>
            <h1 className="mt-1 text-2xl font-black leading-tight [text-shadow:0_1px_8px_rgba(0,0,0,0.12)] sm:text-3xl">{t(greetingKey, { name: firstName })}</h1>
          </div>
          <Mascot pose="saluda" size={112} priority className="relative z-10 -mb-10 shrink-0 animate-float drop-shadow-lg" />
        </div>
      }
    >
      <div className="space-y-4">
        {resume && (
          <section className="animate-rise rounded-[24px] bg-info-soft p-4">
            <div className="flex items-center gap-3">
              <div className="grid size-12 shrink-0 place-items-center rounded-2xl bg-info text-white">
                <SkillIcon skill={resume.skill} className="size-6" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-extrabold leading-tight">{t("today.resume.title")}</p>
                <p className="text-sm text-ink-2">
                  {t("today.resume.body", {
                    skill: t(`skill.${resume.skill}`),
                    scope: scopeLabel(resume.scope, t),
                    done: resume.done,
                    total: resume.total,
                  })}
                </p>
              </div>
            </div>
            <div className="mt-3">
              <ProgressBar value={resume.done} max={resume.total} tone="info" />
            </div>
            <div className="mt-3 flex items-center justify-end gap-2">
              <button
                type="button"
                className="rounded-full px-4 py-2 text-sm font-bold text-ink-2 hover:bg-card"
                onClick={async () => {
                  await discardSession(resume.id);
                  toast(t("today.resume.discarded"));
                }}
              >
                {t("today.resume.discard")}
              </button>
              <ButtonLink href={`/study?id=${resume.id}`} size="sm" className="!bg-info !shadow-none">
                <RotateCcw className="size-4" aria-hidden /> {t("today.resume.cta")}
              </ButtonLink>
            </div>
          </section>
        )}

        {/* Tarjeta principal: lo de hoy */}
        <section className="animate-rise overflow-hidden rounded-[28px] bg-card shadow-soft">
          <div className="relative flex h-40 items-end justify-center overflow-hidden bg-peach">
            <div aria-hidden className="absolute -top-16 left-1/2 size-56 -translate-x-1/2 rounded-full bg-amber/90" />
            <div aria-hidden className="absolute -left-6 bottom-4 h-12 w-32 rounded-full bg-card" />
            <div aria-hidden className="absolute -right-8 bottom-8 h-14 w-36 rounded-full bg-card" />
            <Mascot pose={totalDue + totalNew > 0 ? "celebrando" : "durmiendo"} size={150} className="relative -mb-3" />
          </div>
          <div className="p-5">
            {totalDue + totalNew > 0 ? (
              <>
                <h2 className="text-xl font-black">{t("today.plan.title")}</h2>
                <ul className="mt-3 space-y-2">
                  {counts.map((c) => (
                    <li key={c.skill} className="flex items-center gap-3">
                      <span className={`grid size-8 place-items-center rounded-xl ${skillTone[c.skill].soft} ${skillTone[c.skill].text}`}>
                        <SkillIcon skill={c.skill} className="size-4" />
                      </span>
                      <span className="flex-1 font-bold">{t(`skill.${c.skill}`)}</span>
                      <span className="text-sm font-semibold text-ink-2">
                        {c.due + c.fresh === 0
                          ? t("today.plan.nothing")
                          : [c.due > 0 && tp("today.plan.due", c.due), c.fresh > 0 && tp("today.plan.new", c.fresh)].filter(Boolean).join(" · ")}
                      </span>
                    </li>
                  ))}
                </ul>
                <ButtonLink href={studyHref({ type: "all_due" }, firstSkill ?? "recognition", true)} block size="lg" className="mt-5">
                  <Play className="size-5 fill-current" aria-hidden /> {t("today.plan.cta")}
                </ButtonLink>
                <p className="mt-3 text-center text-xs font-semibold text-ink-3">{t("today.plan.chainHint")}</p>
              </>
            ) : (
              <div className="text-center">
                <h2 className="text-xl font-black">{t("today.plan.allDone.title")}</h2>
                <p className="mt-1 text-ink-2">{t("today.plan.allDone.body")}</p>
              </div>
            )}
          </div>
        </section>

        <StreakCard />
      </div>

      <SectionTitle>{t("today.bySkill")}</SectionTitle>
      <div className="grid grid-cols-3 gap-3">
        {counts.map((c) => {
          const n = c.due + c.fresh;
          return (
            <Link
              key={c.skill}
              href={studyHref({ type: "all_due" }, c.skill)}
              className={`group flex flex-col justify-between rounded-[22px] p-4 transition hover:brightness-[0.98] active:scale-[0.98] ${skillTone[c.skill].soft}`}
            >
              <span className={`grid size-10 place-items-center rounded-2xl text-white ${skillTone[c.skill].strong}`}>
                <SkillIcon skill={c.skill} />
              </span>
              <span className="mt-6 block">
                <span className="block font-extrabold leading-tight">{t(`skill.${c.skill}`)}</span>
                {n > 0 ? (
                  <>
                    {c.due > 0 && <span className="block text-xs font-semibold text-ink-2">{tp("today.plan.due", c.due)}</span>}
                    {c.fresh > 0 && <span className="block text-xs font-semibold text-ink-2">{tp("today.plan.new", c.fresh)}</span>}
                  </>
                ) : (
                  <span className="block text-xs font-semibold text-ink-2">{t("today.plan.nothing")}</span>
                )}
              </span>
            </Link>
          );
        })}
      </div>

      {db.today.recent_decks.length > 0 && (
        <>
          <SectionTitle>{t("today.recentDecks")}</SectionTitle>
          <div className="no-scrollbar -mx-4 flex gap-3 overflow-x-auto px-4 pb-1 sm:-mx-6 sm:px-6">
            {db.today.recent_decks.map((d) => (
              <Link key={d.id} href={`/decks/${d.id}`} className="flex w-64 shrink-0 items-center gap-3 rounded-2xl bg-surface p-2 pr-3 transition hover:brightness-[0.98]">
                <span className="font-hanzi grid size-14 shrink-0 place-items-center rounded-xl text-2xl font-bold text-white" style={{ background: levelColor[d.level] }}>
                  {d.sample}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-extrabold">{t("decks.deckFull", { level: d.level, index: d.index })}</span>
                  <span className="block truncate text-xs font-semibold text-ink-2">{t("deck.counts", { due: d.recognition.due, fresh: d.recognition.new })}</span>
                </span>
                <ChevronRight className="size-4 text-ink-3" aria-hidden />
              </Link>
            ))}
          </div>
        </>
      )}

      <section className="mt-8 flex gap-3 rounded-[22px] bg-peach p-5">
        <Lightbulb className="mt-0.5 size-5 shrink-0 text-amber" aria-hidden />
        <div>
          <p className="font-extrabold">{t("today.tip.title")}</p>
          <p className="mt-1 text-sm leading-relaxed text-ink-2">{t("today.tip.body")}</p>
        </div>
      </section>
    </CurvedPage>
  );
}
