/** Tipos del dominio. Nombres en inglés según la columna "Código" de 02-glosario.md. */

export type LangCode = string; // los idiomas son datos (R-IDI-02): "es", "en", …
export type HskLevel = 1 | 2 | 3 | 4 | 5 | 6;
export type Skill = "recognition" | "listening" | "writing";
export type EditorialStatus = "none" | "draft" | "published";
export type Grade = "pass" | "fail";
export type PosKey = "n" | "v" | "adj" | "adv" | "num" | "mw" | "pron" | "part" | "pn" | "mv";

export interface Sense {
  pos: PosKey;
}

export interface Example {
  zh: string;
  pinyin: string;
  audio?: string | null;
}

/** Contenido por idioma: significados (uno por acepción) y traducciones (una por ejemplo). */
export interface LanguageContent {
  status: EditorialStatus;
  meanings: string[];
  translations: string[];
}

export interface Word {
  id: string;
  hanzi: string;
  pinyin: string;
  level: HskLevel;
  order: number; // número de orden en el sílabo
  hasAudio: boolean;
  audio?: string | null;
  characters?: string[];
  base: { status: EditorialStatus; senses: Sense[]; examples: Example[] };
  content: Partial<Record<LangCode, LanguageContent>>;
}

export type DayStatus = "active" | "exempt" | "missed";

export type SessionScope = { type: "deck"; deckId: string; level?: number; index?: number; themeKeys?: string[]; part?: number | null } | { type: "all_due" };

export interface SessionCard {
  position: number;
  /** Unidad de estudio: id de palabra (lectura/escucha) o carácter (escritura). */
  unit: string;
  /** Palabra de contexto. */
  wordId: string;
  isNew: boolean;
  reinforcement?: boolean;
  result?: Grade | "skipped" | null;
  /** Escucha: las cuatro opciones que fijó el servidor (HU-E04-02). */
  choices?: string[] | null;
}

export interface StudySession {
  id: string;
  scope: SessionScope;
  skill: Skill;
  kind: "scheduled" | "free";
  queue: SessionCard[];
  position: number;
  status: "active" | "completed" | "discarded" | "expired";
  startedAt: string;
  lastActivityAt?: string;
  chain?: boolean; // forma parte de "Estudiar hoy" (R-SES-12)
  summary?: { answered: number; passed: number; failed: number };
}

export type ConsentPurpose = "general" | "reminder_email" | "voice_recording";

export interface Profile {
  name: string;
  uiLanguage: LangCode;
  studyLanguage: LangCode;
  timezone: string;
  newLimitRecognition: number;
  newLimitWriting: number;
  theme: "system" | "light" | "dark";
}

export type ReportElement = "hanzi" | "pinyin" | "meaning" | "example" | "audio" | "strokes" | "other";

export type EmptyReason = "nothing_due" | "new_limit_reached" | "in_review" | "locked";
