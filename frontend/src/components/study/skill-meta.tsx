import { Eye, Headphones, PenLine } from "lucide-react";
import type { SessionScope, Skill } from "@/lib/domain/types";
import type { makeT } from "@/lib/i18n";

export const SKILLS: Skill[] = ["recognition", "listening", "writing"];

export const skillIcon = { recognition: Eye, listening: Headphones, writing: PenLine } as const;

/** Fondo suave y color fuerte de cada habilidad (paleta de feedback). */
export const skillTone: Record<Skill, { soft: string; strong: string; text: string }> = {
  recognition: { soft: "bg-peach", strong: "bg-primary", text: "text-primary" },
  listening: { soft: "bg-info-soft", strong: "bg-info", text: "text-info" },
  writing: { soft: "bg-success-soft", strong: "bg-success", text: "text-success" },
};

export function scopeLabel(scope: SessionScope, t: ReturnType<typeof makeT>["t"]) {
  if (scope.type === "all_due") return t("today.allDueScope");
  return scope.level && scope.index ? t("decks.deckFull", { level: scope.level, index: scope.index }) : "";
}

export function scopeParam(scope: SessionScope) {
  return scope.type === "all_due" ? "all_due" : `deck:${scope.deckId}`;
}

export function parseScope(param: string | null): SessionScope | null {
  if (param === "all_due") return { type: "all_due" };
  if (param?.startsWith("deck:")) {
    const deckId = param.slice(5);
    return /^\d+$/.test(deckId) ? { type: "deck", deckId } : null;
  }
  return null;
}

export function studyHref(scope: SessionScope, skill: Skill, chain = false) {
  return `/study?scope=${encodeURIComponent(scopeParam(scope))}&skill=${skill}${chain ? "&chain=1" : ""}`;
}

export function SkillIcon({ skill, className = "size-5" }: { skill: Skill; className?: string }) {
  const Icon = skillIcon[skill];
  return <Icon className={className} aria-hidden />;
}
