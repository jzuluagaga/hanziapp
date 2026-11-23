"use client";

import { ChevronRight, Search, X } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useDeferredValue, useEffect, useState } from "react";
import { CurvedPage, levelColor } from "@/components/layout/curved-header";
import { Mascot } from "@/components/ui/mascot";
import { Badge, SectionTitle } from "@/components/ui/primitives";
import type { WordListItem } from "@/lib/api/types";
import type { HskLevel } from "@/lib/domain/types";
import { useT } from "@/lib/i18n";
import { loadLevels, loadLevelWords, searchWords } from "@/lib/store/actions";
import { useDb } from "@/lib/store/db";
import { useLoad } from "@/lib/store/use-load";

const LEVELS: HskLevel[] = [1, 2, 3, 4, 5, 6];

export default function DictionaryPage() {
  return (
    <Suspense>
      <Dictionary />
    </Suspense>
  );
}

function Dictionary() {
  const db = useDb();
  const { t, tp } = useT();
  const router = useRouter();
  const params = useSearchParams();
  const [q, setQ] = useState(params.get("q") ?? "");
  const query = useDeferredValue(q);
  const level = Number(params.get("level")) as HskLevel | 0;

  useEffect(() => {
    const sp = new URLSearchParams();
    if (q) sp.set("q", q);
    else if (level) sp.set("level", String(level));
    router.replace(`/dictionary${sp.size ? `?${sp}` : ""}`, { scroll: false });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q]);

  // HU-E07-01: la búsqueda la hace el servidor, solo en el idioma de estudio (R-IDI-07).
  const [results, setResults] = useState<WordListItem[]>([]);
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }
    let live = true;
    const id = setTimeout(() => searchWords(query).then((r) => live && setResults(r)), 250);
    return () => {
      live = false;
      clearTimeout(id);
    };
  }, [query]);
  useLoad(loadLevels, []);
  useLoad(() => (level ? loadLevelWords(level) : null), [level]);
  const levelWords = !query && level ? (db.levelWords[level] ?? []) : [];

  return (
    <CurvedPage
      variant="info"
      header={
        <div className="pt-6">
          <div className="flex items-end justify-between">
            <div className="pb-4">
              <h1 className="text-3xl font-black">{t("dict.title")}</h1>
              <p className="mt-1 font-semibold text-white/90">{t("dict.subtitle")}</p>
            </div>
            <Mascot pose="saluda" size={88} className="-mb-2 drop-shadow-lg" />
          </div>
          <div className="relative mt-2">
            <Search className="pointer-events-none absolute left-4 top-1/2 size-5 -translate-y-1/2 text-ink-3" aria-hidden />
            <label htmlFor="dict-search" className="sr-only">
              {t("dict.search.label")}
            </label>
            <input
              id="dict-search"
              type="search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder={t("dict.search.placeholder")}
              autoComplete="off"
              className="h-13 w-full rounded-full bg-card py-3.5 pl-12 pr-12 text-[15px] font-semibold text-ink shadow-soft outline-none placeholder:font-normal placeholder:text-ink-3 focus:ring-4 focus:ring-white/40 [&::-webkit-search-cancel-button]:hidden"
            />
            {q && (
              <button type="button" onClick={() => setQ("")} aria-label={t("dict.clear")} className="absolute right-2 top-1/2 grid size-9 -translate-y-1/2 place-items-center rounded-full text-ink-2 hover:bg-surface">
                <X className="size-4" />
              </button>
            )}
          </div>
        </div>
      }
    >
      {query ? (
        results.length > 0 ? (
          <>
            <p className="mb-3 text-sm font-bold text-ink-2">{tp("dict.results", results.length)}</p>
            <WordList words={results} from="search" />
          </>
        ) : (
          <div className="flex flex-col items-center py-8 text-center">
            <Mascot pose="triste" size={130} />
            <p className="mt-3 text-lg font-extrabold">{t("dict.noResults", { q: query })}</p>
            <p className="mt-1 max-w-xs text-ink-2">{t("dict.noResults.body")}</p>
          </div>
        )
      ) : level ? (
        <>
          <div className="mb-4 flex items-center justify-between">
            <button type="button" onClick={() => router.replace("/dictionary")} className="text-sm font-bold text-info hover:underline">
              ← {t("dict.byLevel")}
            </button>
            <Badge>{t("common.level", { level })}</Badge>
          </div>
          {levelWords.length ? <WordList words={levelWords} /> : <p className="py-8 text-center font-semibold text-ink-2">{t("dict.level.empty")}</p>}
        </>
      ) : (
        <>
          <p className="text-center text-sm font-semibold text-ink-3">{t("dict.search.hint")}</p>
          <SectionTitle>{t("dict.byLevel")}</SectionTitle>
          <ul className="space-y-3">
            {LEVELS.map((l) => {
              const info = db.levels?.find((x) => x.level === l);
              const n = info?.total ?? 0;
              return (
                <li key={l}>
                  <Link href={`/dictionary?level=${l}`} className="relative flex min-h-24 items-center overflow-hidden rounded-[22px] bg-surface p-5 pr-28 transition hover:brightness-[0.98]">
                    <span>
                      <span className="block font-extrabold">{t("common.level", { level: l })}</span>
                      <span className="block text-sm text-ink-2">{n ? t("dict.level.count", { count: info?.published ?? 0, total: n }) : t("dict.level.empty")}</span>
                    </span>
                    <span aria-hidden className="absolute -right-4 top-1/2 grid size-28 -translate-y-1/2 place-items-center rounded-full text-white" style={{ background: levelColor[l] }}>
                      <span className="font-hanzi -ml-4 text-4xl font-bold">{"汉字语言学习写"[l - 1]}</span>
                    </span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </>
      )}
    </CurvedPage>
  );
}

function WordList({ words, from }: { words: WordListItem[]; from?: "search" }) {
  const { t } = useT();
  return (
    <ul className="divide-y divide-border overflow-hidden rounded-[22px] bg-card shadow-soft">
      {words.map((w) => (
        <li key={w.id}>
          <Link href={`/dictionary/${w.id}${from ? `?from=${from}` : ""}`} className="flex items-center gap-4 px-4 py-3 transition hover:bg-surface/60">
            <span lang="zh-CN" className="font-hanzi w-16 shrink-0 text-2xl">{w.hanzi}</span>
            <span className="min-w-0 flex-1">
              <span className="block text-sm font-bold text-ink-2">{w.pinyin}</span>
              <span className="block truncate text-[15px]">{w.meaning ?? <span className="text-ink-3">{t("badge.in_review")}</span>}</span>
            </span>
            {w.level && <Badge>{t("common.level", { level: w.level })}</Badge>}
            <ChevronRight className="size-4 shrink-0 text-ink-3" aria-hidden />
          </Link>
        </li>
      ))}
    </ul>
  );
}
