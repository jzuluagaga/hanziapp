import type { LangCode, LanguageContent, Word } from "./types";

/** R-CON-04 / R-IDI-06: visible solo si la base y el contenido del idioma de estudio están publicados. */
export function publishedContent(word: Word, lang: LangCode): LanguageContent | null {
  if (word.base.status !== "published") return null;
  const c = word.content[lang];
  return c && c.status === "published" ? c : null;
}

export function isPublished(word: Word, lang: LangCode): boolean {
  return publishedContent(word, lang) !== null;
}

export function primaryMeaning(word: Word, lang: LangCode): string | null {
  return publishedContent(word, lang)?.meanings[0] ?? null;
}

/** Caracteres únicos (hanzi) de una palabra, en orden. */
export function charactersOf(word: Word): string[] {
  return word.characters ?? Array.from(new Set(Array.from(word.hanzi)));
}
