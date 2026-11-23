"use client";

import { Check, Flame, Info } from "lucide-react";
import { useState } from "react";
import { addDays, weekdayIndex } from "@/lib/domain/day";
import { useT } from "@/lib/i18n";
import { useDb } from "@/lib/store/db";
import { dayLogOf, streakOf } from "@/lib/store/selectors";
import { Sheet } from "@/components/ui/primitives";

/** HU-E09-02: veo mi racha y sé qué la mantiene. */
export function StreakCard() {
  const db = useDb();
  const { t, tp } = useT();
  const [open, setOpen] = useState(false);
  const s = streakOf(db);
  const dayLog = dayLogOf(db);
  const counts = db.today?.counts;
  const dueToday = counts ? counts.recognition.due + counts.listening.due + counts.writing.due : 0;
  const status = s.todayActive ? t("streak.todayDone") : dueToday > 0 ? t("streak.todayPending") : t("streak.todayNothing");

  const monday = addDays(s.today, -weekdayIndex(s.today));
  const week = Array.from({ length: 7 }, (_, i) => addDays(monday, i));

  return (
    <section className="rounded-[24px] bg-card p-5 shadow-soft">
      <div className="flex items-center gap-4">
        <div className={`grid size-14 shrink-0 place-items-center rounded-2xl ${s.todayActive ? "bg-amber text-white" : "bg-peach text-amber"}`}>
          <Flame className="size-8" strokeWidth={2.4} aria-hidden />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-xs font-extrabold uppercase tracking-wider text-ink-3">{t("streak.title")}</p>
          <p className="text-2xl font-black leading-tight">{tp("common.days", s.current)}</p>
          <p className="text-sm font-semibold text-ink-2">{status}</p>
        </div>
        <button type="button" onClick={() => setOpen(true)} aria-label={t("streak.how.title")} className="grid size-10 place-items-center rounded-full text-ink-2 hover:bg-surface">
          <Info className="size-5" />
        </button>
      </div>

      <ol className="mt-5 grid grid-cols-7 gap-1.5">
        {week.map((d, i) => {
          const isToday = d === s.today;
          const st = isToday ? (s.todayActive ? "active" : undefined) : dayLog[d];
          const future = d > s.today;
          const label = isToday ? t("day.today") : st ? t(`day.${st}`) : "";
          return (
            <li key={d} className="flex flex-col items-center gap-1.5" aria-label={`${t(`weekday.${i}` as "weekday.0")} ${label}`}>
              <span className={`text-[11px] font-bold ${isToday ? "text-ink" : "text-ink-3"}`}>{t(`weekday.${i}` as "weekday.0")}</span>
              <span
                className={`grid size-9 place-items-center rounded-full text-xs font-black ${
                  st === "active"
                    ? "bg-amber text-white"
                    : st === "exempt"
                      ? "bg-surface text-ink-3"
                      : st === "missed"
                        ? "bg-error-soft text-error"
                        : future
                          ? "border-2 border-dashed border-border"
                          : isToday
                            ? "border-2 border-amber"
                            : "bg-surface"
                }`}
              >
                {st === "active" ? <Check className="size-4" strokeWidth={3.5} aria-hidden /> : st === "exempt" ? "–" : st === "missed" ? "×" : ""}
              </span>
            </li>
          );
        })}
      </ol>
      <p className="mt-4 text-center text-xs font-semibold text-ink-3">{t("streak.max", { value: tp("common.days", s.max) })}</p>

      <Sheet open={open} onClose={() => setOpen(false)} title={t("streak.how.title")}>
        <ul className="space-y-3 text-[15px] leading-snug">
          <li className="flex gap-3">
            <span className="mt-0.5 grid size-7 shrink-0 place-items-center rounded-full bg-amber text-white">
              <Check className="size-4" strokeWidth={3} aria-hidden />
            </span>
            {t("streak.how.active")}
          </li>
          <li className="flex gap-3">
            <span className="mt-0.5 grid size-7 shrink-0 place-items-center rounded-full bg-surface font-black text-ink-3">–</span>
            {t("streak.how.exempt")}
          </li>
          <li className="flex gap-3">
            <span className="mt-0.5 grid size-7 shrink-0 place-items-center rounded-full bg-error-soft font-black text-error">×</span>
            {t("streak.how.missed")}
          </li>
        </ul>
        <div className="mt-5 space-y-1 rounded-2xl bg-peach p-4 text-sm font-semibold text-ink-2">
          <p>{t("streak.how.notCount")}</p>
          <p>{t("streak.how.cutoff")}</p>
        </div>
      </Sheet>
    </section>
  );
}
