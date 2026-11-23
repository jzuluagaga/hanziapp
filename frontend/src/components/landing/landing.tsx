"use client";

import {
  ArrowRight,
  BadgeCheck,
  BookOpen,
  Check,
  ChevronDown,
  CloudUpload,
  Flame,
  Lock,
  MousePointerClick,
  RefreshCcw,
  Smartphone,
  Volume2,
} from "lucide-react";
import Link from "next/link";
import { Clouds } from "@/components/layout/curved-header";
import { SkillIcon, skillTone } from "@/components/study/skill-meta";
import { Logo } from "@/components/ui/logo";
import { Mascot } from "@/components/ui/mascot";
import { CharGrid } from "@/components/word/char-grid";
import { useT, type Key } from "@/lib/i18n";
import { useDb, useHydrated } from "@/lib/store/db";
import { isSignedIn } from "@/lib/store/selectors";
import { PhoneMock } from "./phone-mock";

const SUNRISE = "linear-gradient(170deg, #E84C3D 0%, #F26B35 45%, #FF9F1C 100%)";

function Wrap({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={`mx-auto w-full max-w-6xl px-4 sm:px-6 ${className}`}>{children}</div>;
}

function Eyebrow({ children }: { children: React.ReactNode }) {
  return <p className="text-sm font-extrabold uppercase tracking-[0.14em] text-primary">{children}</p>;
}

function H2({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <h2 className={`mt-2 text-[30px] font-black leading-tight tracking-tight sm:text-4xl ${className}`}>{children}</h2>;
}

/** Botón blanco sobre el degradado de marca. */
const whiteBtn =
  "inline-flex h-14 items-center justify-center gap-2 rounded-full bg-white px-7 text-base font-extrabold text-primary shadow-[0_5px_0_0_rgba(0,0,0,0.12)] transition hover:bg-white/95 active:translate-y-[2px] active:shadow-none";
const ghostWhiteBtn =
  "inline-flex h-14 items-center justify-center gap-2 rounded-full border-2 border-white/70 px-7 text-base font-extrabold text-white transition hover:bg-white/10";
const primaryBtn =
  "inline-flex h-14 items-center justify-center gap-2 rounded-full bg-primary px-7 text-base font-extrabold text-on-color shadow-[0_4px_0_0_var(--primary-hover)] transition hover:bg-primary-hover active:translate-y-[2px] active:shadow-none";

/** HU-E01-01: qué es, para quién y qué es gratis. */
export function Landing() {
  const { t } = useT();
  const db = useDb();
  const hydrated = useHydrated();
  const signedIn = hydrated && isSignedIn(db);
  const ctaHref = signedIn ? "/today" : "/signup";
  const ctaLabel = signedIn ? t("landing.nav.goToApp") : t("landing.hero.cta");

  return (
    <div className="theme-light overflow-x-clip bg-bg text-ink">
      {/* ───────── Hero ───────── */}
      <header className="relative overflow-hidden text-white" style={{ background: SUNRISE }}>
        <Clouds puffs={false} />
        <Wrap className="relative">
          <nav className="flex h-[72px] items-center justify-between gap-3 pt-[env(safe-area-inset-top)]">
            <Logo size={46} />
            <div className="flex items-center gap-1 sm:gap-2">
              {signedIn ? (
                <Link href="/today" className="inline-flex h-11 items-center gap-1.5 whitespace-nowrap rounded-full bg-white px-5 text-sm font-extrabold text-primary shadow-soft">
                  {t("landing.nav.goToApp")} <ArrowRight className="size-4" aria-hidden />
                </Link>
              ) : (
                <>
                  <Link href="/login" className="hidden h-11 items-center whitespace-nowrap rounded-full px-3 text-sm font-extrabold text-white hover:bg-white/15 min-[380px]:inline-flex sm:px-4">
                    {t("landing.nav.login")}
                  </Link>
                  <Link href="/signup" className="inline-flex h-11 items-center whitespace-nowrap rounded-full bg-white px-4 text-sm font-extrabold text-primary shadow-soft hover:bg-white/95 sm:px-5">
                    {t("landing.nav.signup")}
                  </Link>
                </>
              )}
            </div>
          </nav>

          <div className="grid items-center gap-14 pb-32 pt-8 sm:pt-12 lg:grid-cols-[1.1fr_1fr] lg:gap-8 lg:pb-40 lg:pt-16">
            <div className="animate-rise text-center lg:text-left">
              <h1 className="text-[42px] font-black leading-[1.04] tracking-tight [text-shadow:0_2px_14px_rgba(0,0,0,0.12)] sm:text-6xl lg:text-[68px]">
                {t("landing.hero.title")}
              </h1>
              <p className="mx-auto mt-5 max-w-xl text-lg font-semibold leading-relaxed text-white/90 lg:mx-0">{t("landing.hero.subtitle")}</p>
              <div className="mt-8 flex flex-col items-stretch justify-center gap-3 sm:flex-row sm:items-center lg:justify-start">
                <Link href={ctaHref} className={whiteBtn}>
                  {ctaLabel} <ArrowRight className="size-5" aria-hidden />
                </Link>
                {!signedIn && (
                  <Link href="/login" className={ghostWhiteBtn}>
                    {t("landing.hero.secondary")}
                  </Link>
                )}
              </div>
              <p className="mt-4 text-sm font-bold text-white/85">{t("landing.hero.note")}</p>
            </div>
            <div className="animate-rise [animation-delay:120ms]">
              <PhoneMock />
            </div>
          </div>
        </Wrap>
      </header>

      <main className="dome relative -mt-12 bg-bg">
        {/* ───────── Datos clave ───────── */}
        <Wrap className="pt-10">
          <ul className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            {(
              [
                ["landing.facts.levels.value", "landing.facts.levels.label", BadgeCheck, "bg-primary"],
                ["landing.facts.skills.value", "landing.facts.skills.label", MousePointerClick, "bg-success"],
                ["landing.facts.buttons.value", "landing.facts.buttons.label", Check, "bg-info"],
                ["landing.facts.dictionary.value", "landing.facts.dictionary.label", BookOpen, "bg-amber"],
              ] as [Key, Key, typeof Check, string][]
            ).map(([v, l, Icon, color]) => (
              <li key={v} className="rounded-[22px] bg-card p-4 shadow-soft sm:p-5">
                <span className={`grid size-10 place-items-center rounded-xl text-white ${color}`}>
                  <Icon className="size-5" aria-hidden />
                </span>
                <p className="mt-3 text-xl font-black leading-tight sm:text-2xl">{t(v)}</p>
                <p className="mt-0.5 text-sm font-semibold leading-snug text-ink-2">{t(l)}</p>
              </li>
            ))}
          </ul>
        </Wrap>

        {/* ───────── Habilidades ───────── */}
        <Wrap className="pt-24">
          <div className="text-center">
            <Eyebrow>{t("landing.skills.eyebrow")}</Eyebrow>
            <H2>{t("landing.skills.title")}</H2>
          </div>
          <div className="mt-10 grid gap-4 md:grid-cols-3">
            <SkillCard skill="recognition" body={t("landing.skills.recognition.body")}>
              <div className="rounded-3xl bg-card px-8 py-5 text-center shadow-soft">
                <p lang="zh-CN" className="font-hanzi text-6xl leading-none">学习</p>
                <p lang="zh-Latn-pinyin" className="mt-2 font-bold text-ink-2">xuéxí</p>
              </div>
            </SkillCard>
            <SkillCard skill="listening" body={t("landing.skills.listening.body")}>
              <div className="flex flex-col items-center gap-3">
                <span className="grid size-20 place-items-center rounded-full bg-info text-white shadow-[0_6px_0_0_color-mix(in_srgb,var(--info)_70%,black)]">
                  <Volume2 className="size-9" aria-hidden />
                </span>
                <div className="flex gap-2">
                  <span className="rounded-xl border-2 border-success bg-card px-3 py-1.5 text-xs font-bold">{t("landing.mock.meaning")}</span>
                  <span className="rounded-xl border-2 border-border bg-card px-3 py-1.5 text-xs font-bold text-ink-3">…</span>
                </div>
              </div>
            </SkillCard>
            <SkillCard skill="writing" body={t("landing.skills.writing.body")}>
              <div className="relative size-32 rounded-3xl bg-card shadow-soft">
                <CharGrid />
                <p lang="zh-CN" className="font-hanzi absolute inset-0 grid place-items-center text-[88px] leading-none text-border">字</p>
                <p lang="zh-CN" className="font-hanzi absolute inset-0 grid place-items-center text-[88px] leading-none text-success [clip-path:inset(0_0_55%_0)]">字</p>
              </div>
            </SkillCard>
          </div>
        </Wrap>

        {/* ───────── Así funciona ───────── */}
        <Wrap className="pt-24">
          <div className="overflow-hidden rounded-[36px] bg-card p-6 shadow-soft sm:p-10">
            <div className="grid items-center gap-10 lg:grid-cols-[1fr_1.4fr]">
              <div className="text-center lg:text-left">
                <Eyebrow>{t("landing.how.eyebrow")}</Eyebrow>
                <H2>{t("landing.how.title")}</H2>
                <div className="mt-6 hidden justify-center lg:flex lg:justify-start">
                  <Mascot pose="celebrando" size={190} />
                </div>
              </div>
              <ol className="space-y-4">
                {([1, 2, 3] as const).map((n) => (
                  <li key={n} className="flex gap-4 rounded-[24px] bg-surface p-5">
                    <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-primary text-lg font-black text-white">{n}</span>
                    <span>
                      <span className="block text-lg font-extrabold">{t(`landing.how.s${n}.title`)}</span>
                      <span className="mt-0.5 block leading-relaxed text-ink-2">{t(`landing.how.s${n}.body`)}</span>
                    </span>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </Wrap>

        {/* ───────── Características ───────── */}
        <Wrap className="pt-24">
          <div className="text-center">
            <Eyebrow>{t("landing.features.eyebrow")}</Eyebrow>
            <H2>{t("landing.features.title")}</H2>
          </div>
          <ul className="mt-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {(
              [
                ["saved", CloudUpload, "bg-success"],
                ["resume", Smartphone, "bg-info"],
                ["streak", Flame, "bg-amber"],
                ["dictionary", BookOpen, "bg-primary"],
                ["syllabus", BadgeCheck, "bg-hard"],
                ["simple", RefreshCcw, "bg-ink"],
              ] as const
            ).map(([k, Icon, color]) => (
              <li key={k} className="flex gap-4 rounded-[24px] bg-surface p-5">
                <span className={`grid size-12 shrink-0 place-items-center rounded-2xl text-white ${color} ${k === "simple" ? "!text-bg" : ""}`}>
                  <Icon className="size-6" aria-hidden />
                </span>
                <span>
                  <span className="block font-extrabold">{t(`landing.features.${k}.title`)}</span>
                  <span className="mt-0.5 block text-[15px] leading-relaxed text-ink-2">{t(`landing.features.${k}.body`)}</span>
                </span>
              </li>
            ))}
          </ul>
        </Wrap>

        {/* ───────── Racha justa ───────── */}
        <Wrap className="pt-24">
          <div className="grid items-center gap-6 overflow-hidden rounded-[36px] bg-peach p-6 sm:p-10 md:grid-cols-[auto_1fr]">
            <Mascot pose="durmiendo" size={220} className="mx-auto" />
            <div className="text-center md:text-left">
              <H2>{t("landing.rest.title")}</H2>
              <p className="mt-3 max-w-xl text-lg leading-relaxed text-ink-2">{t("landing.rest.body")}</p>
              <ol aria-hidden className="mx-auto mt-6 flex w-fit gap-2 md:mx-0">
                {(["active", "active", "exempt", "active", "active", "active", "today"] as const).map((s, i) => (
                  <li
                    key={i}
                    className={`grid size-10 place-items-center rounded-full text-sm font-black ${
                      s === "active" ? "bg-amber text-white" : s === "exempt" ? "bg-card text-ink-3" : "border-2 border-amber bg-card"
                    }`}
                  >
                    {s === "active" ? <Check className="size-4" strokeWidth={3.5} /> : s === "exempt" ? "–" : ""}
                  </li>
                ))}
              </ol>
              <p className="mt-3 flex items-center justify-center gap-4 text-xs font-bold text-ink-2 md:justify-start">
                <span className="flex items-center gap-1.5">
                  <span className="size-3 rounded-full bg-amber" /> {t("day.active")}
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="size-3 rounded-full bg-card ring-1 ring-border" /> {t("day.exempt")}
                </span>
              </p>
            </div>
          </div>
        </Wrap>

        {/* ───────── Planes ───────── */}
        <Wrap className="pt-24">
          <div className="text-center">
            <Eyebrow>{t("landing.plans.eyebrow")}</Eyebrow>
            <H2>{t("landing.plans.title")}</H2>
          </div>
          <div className="mx-auto mt-10 grid max-w-4xl gap-4 md:grid-cols-2">
            <section className="flex flex-col rounded-[32px] bg-card p-7 shadow-soft ring-2 ring-primary">
              <div className="flex items-center justify-between">
                <h3 className="text-2xl font-black">{t("common.plan.free")}</h3>
                <span className="rounded-full bg-success-soft px-3 py-1 text-sm font-extrabold text-success">{t("landing.plans.free.price")}</span>
              </div>
              <ul className="mt-6 space-y-3">
                {(["landing.plans.free.i1", "landing.plans.free.i2", "landing.plans.free.i3"] as const).map((k) => (
                  <li key={k} className="flex gap-3">
                    <span className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-full bg-success text-white">
                      <Check className="size-3.5" strokeWidth={3.5} aria-hidden />
                    </span>
                    <span className="font-semibold">{t(k)}</span>
                  </li>
                ))}
              </ul>
              <Link href={ctaHref} className={`${primaryBtn} mt-8 w-full`}>
                {ctaLabel}
              </Link>
            </section>
            <section className="flex flex-col rounded-[32px] bg-surface p-7">
              <div className="flex items-center justify-between">
                <h3 className="flex items-center gap-2 text-2xl font-black">
                  {t("common.plan.pro")} <Lock className="size-5 text-ink-3" aria-hidden />
                </h3>
                <span className="rounded-full bg-peach px-3 py-1 text-sm font-extrabold text-ink-2">{t("landing.plans.pro.badge")}</span>
              </div>
              <ul className="mt-6 space-y-3">
                {(["landing.plans.pro.i1", "landing.plans.pro.i2", "landing.plans.pro.i3"] as const).map((k) => (
                  <li key={k} className="flex gap-3">
                    <span className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-full bg-card text-ink-2">
                      <Check className="size-3.5" strokeWidth={3.5} aria-hidden />
                    </span>
                    <span className="font-semibold text-ink-2">{t(k)}</span>
                  </li>
                ))}
              </ul>
            </section>
          </div>
        </Wrap>

        {/* ───────── Preguntas ───────── */}
        <Wrap className="pt-24">
          <H2 className="text-center">{t("landing.faq.title")}</H2>
          <div className="mx-auto mt-8 max-w-3xl space-y-2">
            {([1, 2, 3, 4, 5] as const).map((n) => (
              <details key={n} className="group rounded-[22px] bg-surface open:bg-card open:shadow-soft">
                <summary className="flex cursor-pointer list-none items-center justify-between gap-4 px-5 py-4 text-[17px] font-extrabold [&::-webkit-details-marker]:hidden">
                  {t(`landing.faq.q${n}`)}
                  <ChevronDown className="size-5 shrink-0 transition group-open:rotate-180" aria-hidden />
                </summary>
                <p className="px-5 pb-5 leading-relaxed text-ink-2">{t(`landing.faq.a${n}`)}</p>
              </details>
            ))}
          </div>
        </Wrap>

        {/* ───────── Llamado final ───────── */}
        <Wrap className="pb-16 pt-24">
          <section className="relative overflow-hidden rounded-[40px] px-6 pb-10 pt-6 text-center text-white sm:px-10" style={{ background: SUNRISE }}>
            <Clouds puffs={false} />
            <div className="relative flex flex-col items-center">
              <Mascot pose="celebrando" size={190} className="animate-float drop-shadow-xl" />
              <h2 className="mt-2 text-[32px] font-black leading-tight sm:text-5xl">{t("landing.final.title")}</h2>
              <p className="mt-2 text-lg font-semibold text-white/90">{t("landing.final.body")}</p>
              <Link href={ctaHref} className={`${whiteBtn} mt-7`}>
                {ctaLabel} <ArrowRight className="size-5" aria-hidden />
              </Link>
              {!signedIn && (
                <Link href="/login" className="mt-4 text-sm font-extrabold text-white/90 underline-offset-4 hover:underline">
                  {t("landing.hero.secondary")}
                </Link>
              )}
            </div>
          </section>
        </Wrap>
      </main>

      {/* ───────── Pie ───────── */}
      <footer className="border-t border-border bg-bg">
        <Wrap className="flex flex-col items-center justify-between gap-6 py-10 text-center sm:flex-row sm:text-left">
          <div className="flex flex-col items-center gap-2 sm:items-start">
            <Logo size={40} tone="dark" />
            <p className="text-sm text-ink-2">{t("landing.footer.tagline")}</p>
          </div>
          <nav className="flex flex-wrap justify-center gap-x-6 gap-y-2 text-sm font-bold text-ink-2">
            <Link href="/data-policy" className="hover:text-ink">
              {t("settings.policy")}
            </Link>
            <Link href="/credits" className="hover:text-ink">
              {t("settings.credits")}
            </Link>
            <Link href="/login" className="hover:text-ink">
              {t("landing.nav.login")}
            </Link>
          </nav>
          <p className="text-sm text-ink-3">{t("landing.footer.rights", { year: new Date().getFullYear() })}</p>
        </Wrap>
      </footer>
    </div>
  );
}

function SkillCard({ skill, body, children }: { skill: "recognition" | "listening" | "writing"; body: string; children: React.ReactNode }) {
  const { t } = useT();
  return (
    <article className="overflow-hidden rounded-[32px] bg-card shadow-soft">
      <div className={`grid h-48 place-items-center ${skillTone[skill].soft}`}>{children}</div>
      <div className="p-6">
        <h3 className="flex items-center gap-2.5 text-xl font-black">
          <span className={`grid size-9 place-items-center rounded-xl text-white ${skillTone[skill].strong}`}>
            <SkillIcon skill={skill} className="size-5" />
          </span>
          {t(`skill.${skill}`)}
        </h3>
        <p className="mt-2 leading-relaxed text-ink-2">{body}</p>
      </div>
    </article>
  );
}
