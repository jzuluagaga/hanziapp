"use client";

import { useSyncExternalStore } from "react";
import type { Config, DeckDetail, DeckInfo, LevelInfo, Me, Progress, Today, WordListItem } from "@/lib/api/types";
import type { StudySession, Word } from "@/lib/domain/types";

/** Respuesta en el buzón local, aún sin confirmar por el servidor (R-SES-03, R-SES-04, D-44). */
export interface OutboxItem {
  client_id: string;
  session_id: string;
  position: number;
  unit: string;
  grade: "pass" | "fail";
  choice?: string;
  writing?: { mode: "guided" | "recall"; stroke_misses: number; hint_used: boolean };
  answered_at: string;
  response_ms?: number;
  replays?: number;
  attempts: number;
  first_attempt_at: string;
}

/**
 * Caché del estado del servidor. La fuente de verdad es la API (09-arquitectura.md):
 * aquí solo se guarda lo último que respondió. Persisten en el dispositivo el buzón
 * de respuestas y las sesiones en curso, para que recargar o perder la red no pierda
 * nada (R-SES-04). Las pantallas solo usan `actions.ts` y `selectors.ts`.
 */
export interface Db {
  version: 2;
  auth: "unknown" | "signedIn" | "signedOut";
  me: Me | null;
  config: Config | null;
  today: Today | null;
  sessions: Record<string, StudySession>;
  words: Record<string, Word>;
  levels: LevelInfo[] | null;
  decks: Record<number, DeckInfo[]>;
  deckDetails: Record<string, DeckDetail>;
  levelWords: Record<number, WordListItem[]>;
  progress: Progress | null;
  outbox: OutboxItem[];
  notice: "relocated" | null;
}

export const EMPTY_DB: Db = {
  version: 2,
  auth: "unknown",
  me: null,
  config: null,
  today: null,
  sessions: {},
  words: {},
  levels: null,
  decks: {},
  deckDetails: {},
  levelWords: {},
  progress: null,
  outbox: [],
  notice: null,
};

const KEY = "hanziapp.v2";
const LEGACY_KEY = "hanziapp.db.v1"; // datos de prueba de la maqueta anterior
let state: Db = EMPTY_DB;
let loaded = false;
const listeners = new Set<() => void>();

type Persisted = Pick<Db, "outbox" | "sessions" | "words" | "me">;

function persistable(db: Db): Persisted {
  const sessions = Object.fromEntries(Object.entries(db.sessions).filter(([, s]) => s.status === "active"));
  const wordIds = new Set(Object.values(sessions).flatMap((s) => s.queue.flatMap((c) => [c.wordId, ...(c.choices ?? [])])));
  const words = Object.fromEntries(Object.entries(db.words).filter(([id]) => wordIds.has(id)));
  return { outbox: db.outbox, sessions, words, me: db.me };
}

function load() {
  if (loaded || typeof window === "undefined") return;
  loaded = true;
  try {
    window.localStorage.removeItem(LEGACY_KEY);
    const raw = window.localStorage.getItem(KEY);
    if (raw) state = { ...EMPTY_DB, ...(JSON.parse(raw) as Persisted) };
  } catch {
    state = EMPTY_DB;
  }
  // Otra pestaña confirmó o añadió respuestas: se adopta su buzón (el servidor manda, R-SES-07).
  window.addEventListener("storage", (e) => {
    if (e.key !== KEY || !e.newValue) return;
    try {
      const p = JSON.parse(e.newValue) as Persisted;
      state = { ...state, outbox: p.outbox, sessions: { ...state.sessions, ...p.sessions } };
      listeners.forEach((l) => l());
    } catch {
      /* ignorar */
    }
  });
}

export function getDb(): Db {
  load();
  return state;
}

export function setDb(update: (db: Db) => Db) {
  load();
  state = update(state);
  try {
    window.localStorage.setItem(KEY, JSON.stringify(persistable(state)));
  } catch {
    /* almacenamiento lleno o bloqueado: el estado sigue en memoria */
  }
  listeners.forEach((l) => l());
}

export function resetDb(keep: Partial<Db> = {}) {
  setDb(() => ({ ...EMPTY_DB, ...keep }));
}

function subscribe(cb: () => void) {
  load();
  listeners.add(cb);
  return () => listeners.delete(cb);
}

/** Estado completo; la referencia solo cambia cuando cambian los datos. */
export function useDb(): Db {
  return useSyncExternalStore(subscribe, getDb, () => EMPTY_DB);
}

const noop = () => () => {};
/** false durante el render del servidor y la hidratación; true después. */
export function useHydrated(): boolean {
  return useSyncExternalStore(noop, () => true, () => false);
}
