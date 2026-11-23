"use client";

import { X } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { AuthGate, Splash } from "@/components/layout/auth-gate";
import { ListeningCard } from "@/components/study/listening-card";
import { RecognitionCard } from "@/components/study/recognition-card";
import { EmptyState, SessionSummary } from "@/components/study/session-end";
import { parseScope, scopeLabel, studyHref } from "@/components/study/skill-meta";
import { SyncChip } from "@/components/study/sync-chip";
import { WritingCard } from "@/components/study/writing-card";
import { Button, ButtonLink } from "@/components/ui/button";
import { Container, ProgressBar, Sheet } from "@/components/ui/primitives";
import type { EmptyReason, Grade, Skill } from "@/lib/domain/types";
import { useT } from "@/lib/i18n";
import { answerCard, discardSession, flush, loadToday, recordGuided, resumeSession, startSession, type SessionInfo } from "@/lib/store/actions";
import { useDb } from "@/lib/store/db";
import { profileOf } from "@/lib/store/selectors";

const SKILL_SET = new Set<Skill>(["recognition", "listening", "writing"]);

export default function StudyPage() {
  return (
    <AuthGate>
      <Suspense fallback={<Splash />}>
        <StudyRoute />
      </Suspense>
    </AuthGate>
  );
}

function StudyRoute() {
  const params = useSearchParams();
  // Cada combinación de parámetros es un arranque distinto.
  return <StudyFlow key={params.toString()} />;
}

type Mode =
  | { kind: "loading" }
  | { kind: "session"; id: string }
  | { kind: "conflict"; session: SessionInfo }
  | { kind: "empty"; reason: EmptyReason }
  | { kind: "error"; key: string };

function StudyFlow() {
  const params = useSearchParams();
  const router = useRouter();
  const { t } = useT();
  const [mode, setMode] = useState<Mode>({ kind: "loading" });
  const started = useRef(false);

  const id = params.get("id");
  const scope = parseScope(params.get("scope"));
  const skillParam = params.get("skill") as Skill | null;
  const skill = skillParam && SKILL_SET.has(skillParam) ? skillParam : null;
  const chain = params.get("chain") === "1";

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    (async () => {
      if (id) {
        const s = await resumeSession(id); // R-SES-06
        setMode(s ? { kind: "session", id } : { kind: "error", key: "generic" });
        return;
      }
      if (!scope || !skill) {
        router.replace("/today");
        return;
      }
      const r = await startSession(scope, skill, { chain });
      if (r.type === "started") {
        setMode({ kind: "session", id: r.session.id });
        router.replace(`/study?id=${r.session.id}`); // recargar = reanudar
      } else if (r.type === "conflict") setMode({ kind: "conflict", session: r.session });
      else if (r.type === "empty") setMode({ kind: "empty", reason: r.reason });
      else setMode({ kind: "error", key: r.key });
    })();
  }, [id, scope, skill, chain, router]);

  if (mode.kind === "loading") return <Splash />;

  if (mode.kind === "error") {
    return (
      <Shell onClose={() => router.push("/today")}>
        <div className="flex flex-1 flex-col items-center justify-center gap-4 text-center">
          <p className="font-bold">{t(mode.key === "network" ? "error.network" : "error.generic")}</p>
          <ButtonLink href="/today">{t("session.empty.back")}</ButtonLink>
        </div>
      </Shell>
    );
  }

  if (mode.kind === "empty" && skill) {
    return (
      <Shell onClose={() => router.push("/today")}>
        <EmptyState reason={mode.reason} skill={skill} chain={chain} />
      </Shell>
    );
  }

  if (mode.kind === "conflict") {
    const s = mode.session;
    return (
      <Shell onClose={() => router.push("/today")}>
        <Sheet open onClose={() => router.push("/today")} title={t("session.conflict.title")}>
          <p className="text-ink-2">
            {t("session.conflict.body", { skill: `${t(`skill.${s.skill}`)} · ${scopeLabel(s.scope, t)}`, done: s.done, total: s.total })}
          </p>
          <div className="mt-6 space-y-2">
            <Button block size="lg" onClick={() => router.replace(`/study?id=${s.id}`)}>
              {t("session.conflict.resume")}
            </Button>
            <Button
              block
              variant="ghost"
              onClick={async () => {
                const r = await startSession(s.scope, s.skill, { chain, force: true });
                if (r.type === "started") router.replace(`/study?id=${r.session.id}`);
                else router.replace(studyHref(s.scope, s.skill, chain));
              }}
            >
              {t("session.conflict.discard")}
            </Button>
          </div>
        </Sheet>
      </Shell>
    );
  }

  if (mode.kind === "session") return <SessionView id={mode.id} />;
  return <Splash />;
}

function Shell({ children, onClose, top }: { children: React.ReactNode; onClose: () => void; top?: React.ReactNode }) {
  const { t } = useT();
  return (
    <div className="flex min-h-dvh flex-col bg-bg">
      <Container className="flex items-center gap-3 pb-2 pt-[max(0.75rem,env(safe-area-inset-top))]">
        <button type="button" onClick={onClose} aria-label={t("session.exit.label")} className="-ml-2 grid size-10 shrink-0 place-items-center rounded-full text-ink-2 hover:bg-surface">
          <X className="size-6" />
        </button>
        <div className="flex min-w-0 flex-1 items-center gap-3">{top}</div>
      </Container>
      <Container className="flex flex-1 flex-col pb-2 pt-2">{children}</Container>
    </div>
  );
}

function SessionView({ id }: { id: string }) {
  const db = useDb();
  const { t } = useT();
  const router = useRouter();
  const [exitOpen, setExitOpen] = useState(false);
  const session = db.sessions[id];
  const lang = profileOf(db).studyLanguage;
  const completed = session?.status === "completed";

  const onAnswer = useCallback(
    (g: Grade, extra?: { strokeMisses?: number; usedHint?: boolean; choice?: string; replays?: number; responseMs?: number }) => answerCard(id, g, extra),
    [id],
  );
  const onGuided = useCallback((misses: number) => recordGuided(id, misses), [id]);

  // Al terminar: confirmar lo pendiente y refrescar «Hoy» para la racha del resumen.
  useEffect(() => {
    if (completed) void flush().then(() => loadToday());
  }, [completed]);

  if (!session || session.status === "discarded" || session.status === "expired") {
    return (
      <Shell onClose={() => router.push("/today")}>
        <div className="flex flex-1 flex-col items-center justify-center gap-4 text-center">
          <p className="font-bold">{t("session.notFound")}</p>
          <ButtonLink href="/today">{t("session.empty.back")}</ButtonLink>
        </div>
      </Shell>
    );
  }

  if (completed) {
    return (
      <Shell onClose={() => router.push("/today")}>
        <SessionSummary session={session} />
      </Shell>
    );
  }

  const card = session.queue.find((c) => c.position === session.position);
  const word = card ? db.words[card.wordId] : undefined;
  const done = session.queue.filter((c) => c.result).length;
  if (!card || !word) return <Splash />;

  return (
    <Shell
      onClose={() => setExitOpen(true)}
      top={
        <>
          <div className="flex-1">
            <ProgressBar value={done} max={session.queue.length} tone="amber" label={t("session.progress", { done, total: session.queue.length })} />
          </div>
          <span className="shrink-0 text-xs font-extrabold tabular-nums text-ink-2">{t("session.progress", { done, total: session.queue.length })}</span>
          <SyncChip />
        </>
      }
    >
      {session.skill === "recognition" && <RecognitionCard key={card.position} word={word} card={card} lang={lang} onAnswer={onAnswer} />}
      {session.skill === "listening" && <ListeningCard key={card.position} word={word} card={card} lang={lang} onAnswer={onAnswer} />}
      {session.skill === "writing" && <WritingCard key={card.position} word={word} card={card} lang={lang} onAnswer={onAnswer} onGuided={onGuided} />}

      <Sheet open={exitOpen} onClose={() => setExitOpen(false)} title={t("session.exit.title")}>
        <p className="text-ink-2">{t("session.exit.body")}</p>
        <div className="mt-6 space-y-2">
          <Button block size="lg" onClick={() => setExitOpen(false)}>
            {t("session.exit.keep")}
          </Button>
          <Button block variant="secondary" size="lg" onClick={() => router.push(session.scope.type === "deck" ? `/decks/${session.scope.deckId}` : "/today")}>
            {t("session.exit.leave")}
          </Button>
          <Button
            block
            variant="ghost"
            className="!text-error"
            onClick={async () => {
              await discardSession(session.id);
              router.push("/today");
            }}
          >
            {t("session.exit.discard")}
          </Button>
        </div>
      </Sheet>
    </Shell>
  );
}
