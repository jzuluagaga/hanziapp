"use client";

import { fromProfile, toProfile, toSession, toWord } from "@/lib/api/adapt";
import { api, ApiError } from "@/lib/api/client";
import type {
  AnswerResponse, ApiSession, Config, DeckDetail, DeckInfo, LevelInfo, Me, Progress, SessionSummaryApi, StartResponse, Today,
  WordListItem, ApiWord,
} from "@/lib/api/types";
import { config } from "@/lib/config";
import type { ConsentPurpose, EmptyReason, Grade, Profile, ReportElement, SessionScope, Skill, StudySession } from "@/lib/domain/types";
import { getDb, resetDb, setDb, type OutboxItem } from "./db";

const uid = () => (typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`);
const nowIso = () => new Date().toISOString();
const studyLang = () => getDb().me?.profile.study_language ?? "es";

function onAuthError(e: unknown) {
  if (e instanceof ApiError && e.status === 401) setDb((d) => ({ ...d, auth: "signedOut", me: null }));
  if (e instanceof ApiError && e.status === 428) void loadMe();
}

/* ───────────── Configuración y cuenta ───────────── */

export async function loadConfig(): Promise<Config | null> {
  try {
    const c = await api.get<Config>("/config");
    setDb((d) => ({ ...d, config: c }));
    return c;
  } catch {
    return null;
  }
}

export async function loadMe(): Promise<Me | null> {
  try {
    const me = await api.get<Me>("/me");
    setDb((d) => ({ ...d, me, auth: "signedIn" }));
    return me;
  } catch (e) {
    if (e instanceof ApiError && e.status === 401) setDb((d) => ({ ...d, me: null, auth: "signedOut" }));
    else if (getDb().me) setDb((d) => ({ ...d, auth: "signedIn" })); // sin red: se sigue con lo guardado
    else setDb((d) => ({ ...d, auth: "signedOut" }));
    return null;
  }
}

export type AuthResult = { ok: true } | { ok: false; key: string };

const authError = (e: unknown): AuthResult => ({ ok: false, key: e instanceof ApiError ? e.key : "generic" });

/** HU-E02-02. Las credenciales quedan en cookie httpOnly (Q-11). */
export async function login(email: string, password: string): Promise<AuthResult> {
  try {
    await api.auth("login", { email, password });
    resetDb({ config: getDb().config });
    await loadMe();
    return { ok: true };
  } catch (e) {
    return authError(e);
  }
}

/** HU-E02-01. La cohorte viene del enlace (R-CTA-10). */
export async function register(input: { name: string; email: string; password: string; cohort?: string; reminderConsent: boolean; isAdult: boolean; policyVersion: string }): Promise<AuthResult> {
  try {
    await api.auth("register", {
      name: input.name.trim(),
      email: input.email.trim(),
      password: input.password,
      cohort: input.cohort ?? "",
      reminder_consent: input.reminderConsent,
      is_adult: input.isAdult,
      policy_version: input.policyVersion,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    });
    resetDb({ config: getDb().config });
    await loadMe();
    return { ok: true };
  } catch (e) {
    return authError(e);
  }
}

export async function logout() {
  await flush();
  try {
    await api.auth("logout");
  } finally {
    resetDb({ config: getDb().config, auth: "signedOut" });
  }
}

export async function requestPasswordReset(email: string): Promise<AuthResult> {
  try {
    await api.post("/auth/password-reset", { email });
    return { ok: true };
  } catch (e) {
    return authError(e);
  }
}

export async function confirmPasswordReset(uidParam: string, token: string, newPassword: string): Promise<AuthResult> {
  try {
    await api.post("/auth/password-reset/confirm", { uid: uidParam, token, new_password: newPassword });
    return { ok: true };
  } catch (e) {
    return authError(e);
  }
}

/** HU-E10-03 / R-DAT-06. */
export async function deleteAccount(password: string): Promise<AuthResult> {
  try {
    await api.del("/me", { password });
    resetDb({ config: getDb().config, auth: "signedOut" });
    return { ok: true };
  } catch (e) {
    return authError(e);
  }
}

/** HU-E10-01. */
export async function updateProfile(patch: Partial<Profile>): Promise<AuthResult> {
  try {
    const p = await api.patch<Me["profile"]>("/me/profile", fromProfile(patch));
    setDb((d) => (d.me ? { ...d, me: { ...d.me, profile: p } } : d));
    if (patch.studyLanguage) setDb((d) => ({ ...d, today: null, decks: {}, deckDetails: {}, levelWords: {}, words: {} }));
    return { ok: true };
  } catch (e) {
    onAuthError(e);
    return authError(e);
  }
}

/** HU-E10-02. */
export async function setConsent(purpose: ConsentPurpose, granted: boolean): Promise<AuthResult> {
  try {
    const consents = await api.put<Me["consents"]>(`/me/consents/${purpose}`, { granted });
    setDb((d) => (d.me ? { ...d, me: { ...d.me, consents } } : d));
    return { ok: true };
  } catch (e) {
    return authError(e);
  }
}

export async function acceptPolicy(version: string): Promise<AuthResult> {
  try {
    await api.post("/me/policy/accept", { version });
    await loadMe();
    return { ok: true };
  } catch (e) {
    return authError(e);
  }
}

/* ───────────── Lecturas ───────────── */

async function load<T>(path: string, put: (data: T) => void): Promise<T | null> {
  try {
    const data = await api.get<T>(path);
    put(data);
    return data;
  } catch (e) {
    onAuthError(e);
    return null;
  }
}

export const loadToday = () => load<Today>("/today", (today) => setDb((d) => ({ ...d, today })));
export const loadProgress = () => load<Progress>("/progress", (progress) => setDb((d) => ({ ...d, progress })));
export const loadLevels = () => load<LevelInfo[]>("/levels", (levels) => setDb((d) => ({ ...d, levels })));
export const loadDecks = (level: number) => load<DeckInfo[]>(`/decks?level=${level}`, (list) => setDb((d) => ({ ...d, decks: { ...d.decks, [level]: list } })));
export const loadDeck = (id: string) => load<DeckDetail>(`/decks/${id}`, (detail) => setDb((d) => ({ ...d, deckDetails: { ...d.deckDetails, [id]: detail } })));
export const loadLevelWords = (level: number) =>
  load<WordListItem[]>(`/words?level=${level}`, (list) => setDb((d) => ({ ...d, levelWords: { ...d.levelWords, [level]: list } })));
export const loadWord = (id: string, from?: "search" | "deck" | "card") =>
  load<ApiWord>(`/words/${id}${from ? `?from=${from}` : ""}`, (w) => setDb((d) => ({ ...d, words: { ...d.words, [w.id]: toWord(w, studyLang()) } })));

export async function searchWords(q: string): Promise<WordListItem[]> {
  try {
    return await api.get<WordListItem[]>(`/words/search?q=${encodeURIComponent(q)}`);
  } catch (e) {
    onAuthError(e);
    return [];
  }
}

/** HU-E07-04. */
export async function submitReport(wordId: string, element: ReportElement, comment: string): Promise<AuthResult> {
  try {
    await api.post(`/words/${wordId}/reports`, { element, comment: comment.trim() });
    return { ok: true };
  } catch (e) {
    return authError(e);
  }
}

/** Eventos que nacen en el navegador (Docs/10-api.md §7). Nunca bloquean nada. */
export function track(name: "audio_played" | "audio_failed" | "stroke_order_played" | "writing_hint_shown" | "writing_char_abandoned", props: Record<string, string | number | boolean> = {}) {
  void api.post("/events", { name, props }).catch(() => {});
}

/* ───────────── Sesiones ───────────── */

function storeSession(s: ApiSession): StudySession {
  const session = toSession(s);
  const lang = studyLang();
  setDb((d) => ({
    ...d,
    sessions: { ...d.sessions, [session.id]: session },
    words: { ...d.words, ...Object.fromEntries(Object.entries(s.words).map(([id, w]) => [id, toWord(w, lang)])) },
  }));
  return session;
}

/** Resumen de una sesión en curso para «Hoy» y para el aviso de conflicto. */
export interface SessionInfo {
  id: string;
  scope: SessionScope;
  skill: Skill;
  done: number;
  total: number;
  chain: boolean;
}

export const toInfo = (s: SessionSummaryApi): SessionInfo => ({
  id: s.id,
  scope: s.scope.type === "deck" ? { type: "deck", deckId: String(s.scope.deck_id), level: s.scope.level, index: s.scope.index } : { type: "all_due" },
  skill: s.skill,
  done: s.done,
  total: s.total,
  chain: s.chain,
});

export type StartResult =
  | { type: "started"; session: StudySession }
  | { type: "conflict"; session: SessionInfo }
  | { type: "empty"; reason: EmptyReason }
  | { type: "error"; key: string };

/** HU-E03-01. La cola la arma y la guarda el servidor (R-SES-02). */
export async function startSession(scope: SessionScope, skill: Skill, opts: { chain?: boolean; force?: boolean } = {}): Promise<StartResult> {
  try {
    const r = await api.post<StartResponse>("/sessions", {
      scope: scope.type === "deck" ? { type: "deck", deck_id: scope.deckId } : { type: "all_due" },
      skill,
      chain: !!opts.chain,
      force: !!opts.force,
    });
    if (!r.session) return { type: "empty", reason: r.empty_reason };
    return { type: "started", session: storeSession(r.session) };
  } catch (e) {
    if (e instanceof ApiError && e.status === 409) return { type: "conflict", session: toInfo(e.body.session as SessionSummaryApi) };
    onAuthError(e);
    return { type: "error", key: e instanceof ApiError ? e.key : "generic" };
  }
}

/**
 * HU-E06-02: reanudar en la primera tarjeta sin responder. Primero se vacía el buzón;
 * sin red se sigue con la copia local de la sesión.
 */
export async function resumeSession(id: string): Promise<StudySession | null> {
  await flush();
  if (getDb().outbox.some((o) => o.session_id === id)) return getDb().sessions[id] ?? null;
  try {
    const r = await api.post<{ session: ApiSession }>(`/sessions/${id}/resume`, { same_client: !!getDb().sessions[id] });
    return storeSession(r.session);
  } catch (e) {
    onAuthError(e);
    return getDb().sessions[id] ?? null;
  }
}

export async function reloadSession(id: string): Promise<StudySession | null> {
  try {
    const r = await api.get<{ session: ApiSession }>(`/sessions/${id}`);
    return storeSession(r.session);
  } catch {
    return getDb().sessions[id] ?? null;
  }
}

/** R-SES-08: lo ya respondido es definitivo. */
export async function discardSession(id: string) {
  await flush();
  setDb((d) => {
    const s = d.sessions[id];
    return s ? { ...d, sessions: { ...d.sessions, [id]: { ...s, status: "discarded" } } } : d;
  });
  try {
    await api.post(`/sessions/${id}/discard`);
  } catch (e) {
    onAuthError(e);
  }
  void loadToday();
}

/**
 * Respuesta optimista (flujo 1 de 09-arquitectura.md): la siguiente tarjeta aparece sin
 * esperar a la red (Q-03); la respuesta va al buzón y se envía después. El servidor
 * recalcula la calificación en escucha y escritura; aquí se aplica la misma regla para
 * que la pantalla no espere.
 */
export function answerCard(
  sessionId: string,
  grade: Grade,
  extra: { strokeMisses?: number; usedHint?: boolean; choice?: string; responseMs?: number; replays?: number } = {},
) {
  const s = getDb().sessions[sessionId];
  if (!s || s.status !== "active") return;
  const card = s.queue.find((c) => c.position === s.position);
  if (!card || card.result) return;

  let g = grade;
  if (s.skill === "writing") g = !extra.usedHint && (extra.strokeMisses ?? 0) <= config.writingMaxStrokeMisses ? "pass" : "fail";
  if (s.skill === "listening" && extra.choice) g = extra.choice === card.wordId ? "pass" : "fail";

  let queue = s.queue.map((c) => (c.position === card.position ? { ...c, result: g } : c));
  if (g === "fail") {
    // R-REP-05: el refuerzo entra tras `reinforceGap` tarjetas, igual que en el servidor.
    const at = Math.min(card.position + 1 + config.reinforceGap, queue.length);
    queue = queue.map((c) => (c.position >= at ? { ...c, position: c.position + 1 } : c));
    queue.push({ position: at, unit: card.unit, wordId: card.wordId, isNew: false, reinforcement: true, result: null, choices: card.choices });
    queue.sort((a, b) => a.position - b.position);
  }
  const next = queue.find((c) => !c.result);
  const item: OutboxItem = {
    client_id: uid(),
    session_id: sessionId,
    position: card.position,
    unit: card.unit,
    grade: g,
    answered_at: nowIso(),
    attempts: 0,
    first_attempt_at: nowIso(),
    ...(extra.choice ? { choice: extra.choice } : {}),
    ...(extra.responseMs !== undefined ? { response_ms: Math.round(extra.responseMs) } : {}),
    ...(extra.replays !== undefined ? { replays: extra.replays } : {}),
    ...(s.skill === "writing" ? { writing: { mode: "recall" as const, stroke_misses: extra.strokeMisses ?? 0, hint_used: !!extra.usedHint } } : {}),
  };
  setDb((d) => ({
    ...d,
    outbox: [...d.outbox, item],
    sessions: {
      ...d.sessions,
      [sessionId]: { ...s, queue, position: next ? next.position : queue.length, status: next ? "active" : "completed", lastActivityAt: nowIso() },
    },
  }));
  scheduleFlush(0);
}

/** Práctica con guía de un carácter nuevo: se registra y no consume la tarjeta (R-ESC-02, R-ESC-06). */
export function recordGuided(sessionId: string, strokeMisses: number) {
  const s = getDb().sessions[sessionId];
  const card = s?.queue.find((c) => c.position === s.position);
  if (!s || !card) return;
  const item: OutboxItem = {
    client_id: uid(), session_id: sessionId, position: card.position, unit: card.unit, grade: "pass",
    writing: { mode: "guided", stroke_misses: strokeMisses, hint_used: false }, answered_at: nowIso(), attempts: 0, first_attempt_at: nowIso(),
  };
  setDb((d) => ({ ...d, outbox: [...d.outbox, item] }));
  scheduleFlush(0);
}

/* ───────────── Envío del buzón (R-SES-03 / R-SES-04) ───────────── */

let flushing: Promise<void> | null = null;
let timer: ReturnType<typeof setTimeout> | null = null;
let backoff = 1000;

export function scheduleFlush(delay = backoff) {
  if (typeof window === "undefined") return;
  if (timer) clearTimeout(timer);
  timer = setTimeout(() => {
    timer = null;
    void flush();
  }, delay);
}

const removeItem = (id: string) => setDb((d) => ({ ...d, outbox: d.outbox.filter((o) => o.client_id !== id) }));

/** Envía en orden, de uno en uno. Cada identificador se aplica una sola vez en el servidor. */
export function flush(): Promise<void> {
  if (flushing) return flushing;
  flushing = (async () => {
    const touched = new Set<string>();
    let relocated = false;
    while (getDb().outbox.length) {
      const item = getDb().outbox[0];
      const attempts = item.attempts + 1;
      try {
        const r = await api.post<AnswerResponse>("/answers", { ...item, attempts });
        removeItem(item.client_id);
        backoff = 1000;
        const local = getDb().sessions[item.session_id];
        if (local && !getDb().outbox.some((o) => o.session_id === item.session_id) && local.position !== r.session.position) touched.add(item.session_id);
        if (r.session.status === "completed") touched.add(item.session_id);
      } catch (e) {
        if (e instanceof ApiError && e.status === 409) {
          removeItem(item.client_id); // R-SES-07: ganó otra respuesta; esta no tiene efecto
          touched.add(item.session_id);
          relocated = true;
        } else if (e instanceof ApiError && (e.status === 0 || e.status >= 500 || e.status === 429)) {
          setDb((d) => ({ ...d, outbox: d.outbox.map((o) => (o.client_id === item.client_id ? { ...o, attempts } : o)) }));
          backoff = Math.min(backoff * 2, 30_000);
          scheduleFlush(backoff);
          break;
        } else if (e instanceof ApiError && (e.status === 401 || e.status === 428)) {
          onAuthError(e);
          break;
        } else {
          removeItem(item.client_id); // petición inválida: reintentarla no la arreglará
        }
      }
    }
    for (const id of touched) if (!getDb().outbox.some((o) => o.session_id === id)) await reloadSession(id);
    if (relocated) setDb((d) => ({ ...d, notice: "relocated" }));
  })().finally(() => {
    flushing = null;
  });
  return flushing;
}

export const clearNotice = () => setDb((d) => ({ ...d, notice: null }));

export { toProfile };
