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

type T = ReturnType<typeof makeT>["t"];

/**
 * Nombre de un mazo del sistema (D-49): los nombres de sus temas unidos por " · " y "Parte n"
 * si la tiene. Un mazo sin temas (nivel aún sin aprobar) se llama por número: "Parte 3".
 * Con `withLevel`, antepone el nivel: "HSK 1 · Comida y bebida".
 */
export function deckLabel(t: T, d: { level?: number; index?: number; themeKeys?: string[]; part?: number | null }, withLevel = false) {
  const keys = d.themeKeys ?? [];
  const name = keys.length
    ? [...keys.map((k) => t(`theme.${k}` as "theme.food_drink")), ...(d.part ? [t("decks.part", { n: d.part })] : [])].join(" · ")
    : t("decks.deckName", { index: d.index ?? 0 });
  return withLevel && d.level ? `${t("common.level", { level: d.level })} · ${name}` : name;
}

export function scopeLabel(scope: SessionScope, t: T) {
  if (scope.type === "all_due") return t("today.allDueScope");
  return deckLabel(t, scope, true);
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
