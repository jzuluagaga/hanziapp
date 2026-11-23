/** Traduce las formas de la API a los tipos de dominio que usan los componentes. */
import type { Profile, SessionCard, SessionScope, StudySession, Word } from "@/lib/domain/types";
import type { ApiCard, ApiProfile, ApiScope, ApiSession, ApiWord } from "./types";

export function toWord(w: ApiWord, lang: string): Word {
  const published = w.editorial === "published";
  return {
    id: w.id,
    hanzi: w.hanzi,
    pinyin: w.pinyin,
    level: w.level,
    order: w.order,
    hasAudio: !!w.audio,
    audio: w.audio,
    characters: w.characters,
    base: {
      status: published ? "published" : "none",
      senses: w.senses.map((s) => ({ pos: s.pos })),
      examples: w.examples.map((e) => ({ zh: e.zh, pinyin: e.pinyin, audio: e.audio })),
    },
    content: published
      ? { [lang]: { status: "published", meanings: w.senses.map((s) => s.meaning), translations: w.examples.map((e) => e.translation) } }
      : {},
  };
}

export const toScope = (s: ApiScope): SessionScope =>
  s.type === "deck"
    ? { type: "deck", deckId: String(s.deck_id), level: s.level, index: s.index, themeKeys: s.theme_keys, part: s.part }
    : { type: "all_due" };

export const toCard = (c: ApiCard): SessionCard => ({
  position: c.position,
  unit: c.unit,
  wordId: c.word_id,
  isNew: c.is_new,
  reinforcement: c.is_reinforcement,
  result: c.result,
  choices: c.choices,
});

export function toSession(s: ApiSession): StudySession {
  return {
    id: s.id,
    scope: toScope(s.scope),
    skill: s.skill,
    kind: s.kind,
    queue: [...s.cards].sort((a, b) => a.position - b.position).map(toCard),
    position: s.position,
    status: s.status,
    startedAt: s.started_at,
    chain: s.chain,
    summary: s.summary,
  };
}

export const toProfile = (p: ApiProfile): Profile => ({
  name: p.name,
  uiLanguage: p.ui_language,
  studyLanguage: p.study_language,
  timezone: p.timezone,
  newLimitRecognition: p.new_limit_recognition,
  newLimitWriting: p.new_limit_writing,
  theme: p.theme,
});

export const fromProfile = (p: Partial<Profile>): Partial<ApiProfile> => {
  const out: Partial<ApiProfile> = {};
  if (p.name !== undefined) out.name = p.name;
  if (p.uiLanguage !== undefined) out.ui_language = p.uiLanguage;
  if (p.studyLanguage !== undefined) out.study_language = p.studyLanguage;
  if (p.timezone !== undefined) out.timezone = p.timezone;
  if (p.newLimitRecognition !== undefined) out.new_limit_recognition = p.newLimitRecognition;
  if (p.newLimitWriting !== undefined) out.new_limit_writing = p.newLimitWriting;
  if (p.theme !== undefined) out.theme = p.theme;
  return out;
};
