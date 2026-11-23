"use client";

import { ChevronLeft, ChevronRight, Lock } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { CurvedPage, levelVariant } from "@/components/layout/curved-header";
import { SKILLS, SkillIcon, skillTone, studyHref } from "@/components/study/skill-meta";
import { Badge, Container, SectionTitle } from "@/components/ui/primitives";
import { Splash } from "@/components/layout/auth-gate";
import { useT } from "@/lib/i18n";
import { loadDeck } from "@/lib/store/actions";
import { useDb } from "@/lib/store/db";
import { useLoad } from "@/lib/store/use-load";

const badgeTone = { new: "info", due: "hard", learned: "success", scheduled: "neutral", in_review: "neutral" } as const;

export default function DeckPage() {
  const { deckId } = useParams<{ deckId: string }>();
  const db = useDb();
  const { t, tp } = useT();
  const [missing, setMissing] = useState(false);
  useLoad(() => loadDeck(deckId).then((d) => setMissing(!d)), [deckId]);
  const detail = db.deckDetails[deckId];
  if (!detail && !missing) return <Splash />;
  const deck = detail?.deck;
  if (!deck) {
    return (
      <Container className="py-16 text-center">
        <p className="font-bold">{t("deck.notFound")}</p>
      </Container>
    );
  }
  const allowed = !deck.locked;
  const scope = { type: "deck" as const, deckId: deck.id };

  return (
    <CurvedPage
      variant={levelVariant[deck.level]}
      header={
        <div className="pt-2">
          <Link href={`/decks?level=${deck.level}`} aria-label={t("common.back")} className="-ml-2 grid size-10 place-items-center rounded-full hover:bg-white/15">
            <ChevronLeft className="size-6" />
          </Link>
          <div className="pb-2 pt-3 text-center">
            <p className="text-sm font-bold text-white/85">{t("common.level", { level: deck.level })}</p>
            <h1 className="text-3xl font-black">{t("decks.deckName", { index: deck.index })}</h1>
            <p className="mt-1 font-semibold text-white/90">{tp("common.words", deck.size)}</p>
          </div>
        </div>
      }
    >
      <SectionTitle>{t("deck.study")}</SectionTitle>
      <div className="space-y-3">
        {SKILLS.map((skill) => {
          const c = { due: deck.counts[skill].due, fresh: deck.counts[skill].new };
          const n = c.due + c.fresh;
          return (
            <Link
              key={skill}
              href={allowed ? studyHref(scope, skill) : "#"}
              aria-disabled={!allowed}
              className={`flex items-center gap-4 rounded-[22px] bg-surface p-3 pr-4 transition hover:brightness-[0.98] ${!allowed ? "pointer-events-none opacity-60" : ""}`}
            >
              <span className={`grid size-14 shrink-0 place-items-center rounded-2xl text-white ${skillTone[skill].strong}`}>
                <SkillIcon skill={skill} className="size-6" />
              </span>
              <span className="min-w-0 flex-1">
                <span className="block font-extrabold">{t(`skill.${skill}`)}</span>
                <span className="block truncate text-sm text-ink-2">{t(`skill.${skill}.desc`)}</span>
              </span>
              {!allowed ? (
                <Lock className="size-5 text-ink-3" aria-label={t("common.locked")} />
              ) : (
                <>
                  <span className="text-right text-sm font-bold text-ink-2">{n > 0 ? t("deck.counts", { due: c.due, fresh: c.fresh }) : t("today.plan.nothing")}</span>
                  <ChevronRight className="size-5 shrink-0" aria-hidden />
                </>
              )}
            </Link>
          );
        })}
      </div>

      <SectionTitle>{t("deck.words")}</SectionTitle>
      <ul className="divide-y divide-border overflow-hidden rounded-[22px] bg-card shadow-soft">
        {detail.words.map((w) => {
          const badge = w.badge ?? "in_review";
          return (
            <li key={w.id}>
              <Link href={`/dictionary/${w.id}?from=deck`} className="flex items-center gap-4 px-4 py-3 transition hover:bg-surface/60">
                <span className="font-hanzi w-16 shrink-0 text-2xl font-medium">{w.hanzi}</span>
                <span className="min-w-0 flex-1">
                  <span className="block text-sm font-bold text-ink-2">{w.pinyin}</span>
                  <span className="block truncate text-[15px]">{w.meaning ?? "—"}</span>
                </span>
                <Badge tone={badgeTone[badge]}>{t(`badge.${badge}`)}</Badge>
              </Link>
            </li>
          );
        })}
      </ul>
    </CurvedPage>
  );
}
