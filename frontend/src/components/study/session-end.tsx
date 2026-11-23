"use client";

import { Flame, SkipForward } from "lucide-react";
import { useRouter } from "next/navigation";
import { Button, ButtonLink } from "@/components/ui/button";
import { Mascot, type MascotPose } from "@/components/ui/mascot";
import type { EmptyReason, Skill, StudySession } from "@/lib/domain/types";
import { useT } from "@/lib/i18n";
import { useDb } from "@/lib/store/db";
import { streakOf } from "@/lib/store/selectors";
import { SKILLS, SkillIcon, studyHref } from "./skill-meta";

/** Siguiente habilidad en "Estudiar hoy" (R-SES-12). */
export function nextSkill(skill: Skill): Skill | null {
  const i = SKILLS.indexOf(skill);
  return SKILLS[i + 1] ?? null;
}

function ChainActions({ skill }: { skill: Skill }) {
  const { t } = useT();
  const router = useRouter();
  const next = nextSkill(skill);
  if (!next) return null;
  const after = nextSkill(next);
  return (
    <div className="space-y-2">
      <Button block size="lg" onClick={() => router.replace(studyHref({ type: "all_due" }, next, true))}>
        <SkillIcon skill={next} /> {t("summary.next", { skill: t(`skill.${next}`).toLowerCase() })}
      </Button>
      <Button
        block
        variant="ghost"
        onClick={() => router.replace(after ? studyHref({ type: "all_due" }, after, true) : "/today")}
      >
        <SkipForward className="size-4" aria-hidden /> {t("summary.skip", { skill: t(`skill.${next}`).toLowerCase() })}
      </Button>
    </div>
  );
}

/** HU-E03-04: al terminar veo aciertos, fallos y qué sigue. */
export function SessionSummary({ session }: { session: StudySession }) {
  const { t, tp } = useT();
  const db = useDb();
  const streak = streakOf(db);
  const main = session.queue.filter((c) => !c.reinforcement);
  const passed = main.filter((c) => c.result === "pass").length;
  const failed = main.filter((c) => c.result === "fail").length;
  const skipped = main.filter((c) => c.result === "skipped").length;
  const reinf = session.queue.filter((c) => c.reinforcement && c.result).length;
  const pose: MascotPose = passed >= failed ? "celebrando" : "saluda";
  const backHref = session.scope.type === "deck" ? `/decks/${session.scope.deckId}` : "/today";
  const chainNext = session.chain ? nextSkill(session.skill) : null;

  return (
    <div className="flex flex-1 flex-col items-center pb-6 text-center">
      <Mascot pose={pose} size={200} className="animate-pop mt-2" priority />
      <h1 className="mt-2 text-3xl font-black">{chainNext === null && session.chain ? t("summary.chainDone") : t("summary.title")}</h1>
      <p className="mt-1 font-bold text-ink-2">{t(`skill.${session.skill}`)}</p>

      <div className="mt-6 grid w-full grid-cols-2 gap-3">
        <div className="rounded-[22px] bg-success-soft p-4">
          <p className="text-3xl font-black text-success">{passed}</p>
          <p className="text-sm font-bold text-ink-2">{t("summary.passed")}</p>
        </div>
        <div className="rounded-[22px] bg-error-soft p-4">
          <p className="text-3xl font-black text-error">{failed}</p>
          <p className="text-sm font-bold text-ink-2">{t("summary.failed")}</p>
        </div>
      </div>
      {reinf > 0 && <p className="mt-3 text-sm font-semibold text-ink-2">{`${t("summary.reinforcements")}: ${reinf}`}</p>}
      {skipped > 0 && <p className="mt-1 text-sm font-semibold text-ink-3">{tp("summary.skippedInfo", skipped)}</p>}

      {streak.todayActive && (
        <div className="mt-5 flex w-full items-center gap-3 rounded-[22px] bg-peach p-4 text-left">
          <span className="grid size-11 place-items-center rounded-2xl bg-amber text-white">
            <Flame className="size-6" aria-hidden />
          </span>
          <span>
            <span className="block font-extrabold">{t("summary.streakActive")}</span>
            <span className="block text-sm font-semibold text-ink-2">{t("summary.streak", { value: tp("common.days", streak.current) })}</span>
          </span>
        </div>
      )}

      <div className="mt-auto w-full space-y-2 pt-8">
        {session.chain && chainNext ? (
          <ChainActions skill={session.skill} />
        ) : (
          <ButtonLink href={backHref} block size="lg">
            {session.scope.type === "deck" ? t("summary.backToDeck") : t("summary.done")}
          </ButtonLink>
        )}
      </div>
    </div>
  );
}

const emptyPose: Record<EmptyReason, MascotPose> = {
  nothing_due: "durmiendo",
  new_limit_reached: "celebrando",
  in_review: "saluda",
  locked: "triste",
};

/** R-SES-10: no se crea una sesión vacía; se dice por qué. */
export function EmptyState({ reason, skill, chain }: { reason: EmptyReason; skill: Skill; chain: boolean }) {
  const { t } = useT();
  return (
    <div className="flex flex-1 flex-col items-center pb-6 text-center">
      <Mascot pose={emptyPose[reason]} size={190} className="animate-pop mt-6" priority />
      <p className="mt-2 text-sm font-bold text-ink-3">{t(`skill.${skill}`)}</p>
      <h1 className="mt-1 text-2xl font-black">{t(`session.empty.${reason}.title`)}</h1>
      <p className="mt-2 max-w-sm text-ink-2">{t(`session.empty.${reason}.body`)}</p>
      <div className="mt-auto w-full space-y-2 pt-8">
        {chain && nextSkill(skill) ? (
          <ChainActions skill={skill} />
        ) : (
          <ButtonLink href="/today" block size="lg">
            {t("session.empty.back")}
          </ButtonLink>
        )}
        {reason === "new_limit_reached" && (
          <ButtonLink href="/me/settings/profile" variant="ghost" block>
            {t("session.empty.changeLimits")}
          </ButtonLink>
        )}
      </div>
    </div>
  );
}
