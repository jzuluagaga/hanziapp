"use client";

import { useMemo } from "react";
import { useDb } from "@/lib/store/db";
import type { LangCode } from "@/lib/domain/types";
import { en } from "./en";
import { es, type Key } from "./es";

export type { Key };
type PluralBase<K = Key> = K extends `${infer B}.one` ? B : never;
type Vars = Record<string, string | number>;

const CATALOGS: Record<string, Record<Key, string>> = { es, en };

function interpolate(s: string, vars?: Vars) {
  if (!vars) return s;
  return s.replace(/\{(\w+)\}/g, (_, k: string) => (vars[k] !== undefined ? String(vars[k]) : `{${k}}`));
}

export function makeT(lang: LangCode) {
  const cat = CATALOGS[lang] ?? es;
  const plural = new Intl.PluralRules(lang);
  const t = (key: Key, vars?: Vars) => interpolate(cat[key], vars);
  /** Plurales: busca `${base}.one` / `${base}.other` según las reglas del idioma. */
  const tp = (base: PluralBase, count: number, vars?: Vars) => {
    const form = plural.select(count) === "one" ? "one" : "other";
    return interpolate(cat[`${base}.${form}` as Key], { count, ...vars });
  };
  return { t, tp, lang };
}

/** Idioma de interfaz del perfil, solo si está activo (R-IDI-02) y tiene catálogo; si no, español. */
export function useT() {
  const db = useDb();
  const wanted = db.me?.profile.ui_language ?? "es";
  const active = db.config ? db.config.languages.some((l) => l.code === wanted && l.is_ui_active) : wanted === "es";
  const lang: LangCode = active && CATALOGS[wanted] ? wanted : "es";
  return useMemo(() => makeT(lang), [lang]);
}
