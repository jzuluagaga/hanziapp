/** Formas de la API (Docs/10-api.md). */
import type { DayStatus, EmptyReason, HskLevel, PosKey, Skill } from "@/lib/domain/types";

export type Counts = Record<Skill, { due: number; new: number }>;

export interface ApiProfile {
  name: string;
  ui_language: string;
  study_language: string;
  timezone: string;
  new_limit_recognition: number;
  new_limit_writing: number;
  theme: "system" | "light" | "dark";
}

export interface Me {
  account: { id: string; email: string; email_verified: boolean; cohort: string; created_at: string };
  profile: ApiProfile;
  plan: string;
  entitlements: { levels: number[]; own_decks_max: number };
  consents: Record<"general" | "reminder_email" | "voice_recording", boolean>;
  policy: { current: string; accepted: string | null; accepted_at: string | null; required: boolean };
  today: string;
}

export interface Config {
  languages: { code: string; is_study_active: boolean; is_ui_active: boolean }[];
  policy_version: string;
  signup_mode: "open" | "closed";
  limits: Record<"new_limit_recognition" | "new_limit_writing", { min: number; max: number; default: number }>;
}

export interface ApiScope {
  type: "all_due" | "deck";
  deck_id?: string;
  level?: number;
  index?: number;
  theme_keys?: string[];
  part?: number | null;
}

export interface SessionSummaryApi {
  id: string;
  scope: ApiScope;
  skill: Skill;
  kind: "scheduled" | "free";
  status: "active" | "completed" | "discarded" | "expired";
  chain: boolean;
  position: number;
  total: number;
  done: number;
  last_activity_at: string;
}

export interface Today {
  today: string;
  counts: Counts;
  active_sessions: SessionSummaryApi[];
  streak: { current: number; max: number; today_active: boolean };
  recent_decks: { id: string; level: HskLevel; index: number; theme_keys: string[]; part: number | null; sample: string; recognition: { due: number; new: number } }[];
  days: { day: string; status: DayStatus }[];
}

export interface ApiWord {
  id: string;
  hanzi: string;
  pinyin: string;
  level: HskLevel;
  order: number;
  editorial: "published" | "in_review";
  senses: { pos: PosKey; meaning: string; reading: string }[];
  examples: { zh: string; pinyin: string; translation: string; audio: string | null }[];
  characters: string[];
  audio: string | null;
}

export interface ApiCard {
  position: number;
  unit: string;
  unit_kind: "word" | "character";
  word_id: string;
  is_new: boolean;
  is_reinforcement: boolean;
  result: "pass" | "fail" | "skipped" | null;
  choices: string[] | null;
}

export interface ApiSession {
  id: string;
  scope: ApiScope;
  skill: Skill;
  kind: "scheduled" | "free";
  status: "active" | "completed" | "discarded" | "expired";
  chain: boolean;
  position: number;
  started_at: string;
  cards: ApiCard[];
  words: Record<string, ApiWord>;
  summary: { answered: number; passed: number; failed: number };
}

export interface AnswerResponse {
  answer: { client_id: string; grade: "pass" | "fail"; counted: boolean; introduced_new: boolean };
  session: { status: ApiSession["status"]; position: number; cards_added: ApiCard[] };
}

export interface LevelInfo {
  level: HskLevel;
  total: number;
  published: number;
  locked: boolean;
  unlocking_plan: string | null;
  decks: number;
}

export interface DeckInfo {
  id: string;
  kind: "system" | "own";
  level: HskLevel;
  index: number;
  theme_keys: string[];
  part: number | null;
  size: number;
  published: number;
  locked: boolean;
  unlocking_plan: string | null;
  counts: Counts;
}

export interface WordListItem {
  id: string;
  hanzi: string;
  pinyin: string;
  level?: HskLevel;
  meaning: string | null;
  editorial: "published" | "in_review";
  badge?: "in_review" | "new" | "due" | "learned" | "scheduled";
}

export interface DeckDetail {
  deck: DeckInfo;
  words: WordListItem[];
}

export interface Progress {
  learned_words: number;
  learned_chars: number;
  total_answers: number;
  levels: { level: HskLevel; total: number; published: number; learned: number }[];
  streak: Today["streak"];
  days: { day: string; status: DayStatus }[];
}

export type StartResponse = { session: ApiSession } | { session: null; empty_reason: EmptyReason };
