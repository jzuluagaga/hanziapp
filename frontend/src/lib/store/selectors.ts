import { toProfile } from "@/lib/api/adapt";
import { config } from "@/lib/config";
import { localDay } from "@/lib/domain/day";
import type { DayStatus, Profile } from "@/lib/domain/types";
import { toInfo, type SessionInfo } from "./actions";
import type { Db } from "./db";

export const DEFAULT_PROFILE: Profile = {
  name: "",
  uiLanguage: "es",
  studyLanguage: "es",
  timezone: "America/Bogota",
  newLimitRecognition: config.newLimitRecognition.default,
  newLimitWriting: config.newLimitWriting.default,
  theme: "system",
};

export const profileOf = (db: Db): Profile => (db.me ? toProfile(db.me.profile) : DEFAULT_PROFILE);
export const todayOf = (db: Db): string => db.today?.today ?? db.me?.today ?? localDay(new Date(), profileOf(db).timezone);
export const isSignedIn = (db: Db) => db.auth === "signedIn" && !!db.me;
export const canStudyLevel = (db: Db, level: number) => !!db.me?.entitlements.levels.includes(level);

export function streakOf(db: Db) {
  const s = db.today?.streak ?? db.progress?.streak ?? { current: 0, max: 0, today_active: false };
  return { current: s.current, max: s.max, todayActive: s.today_active, today: todayOf(db) };
}

/** Estados de los días ya cerrados, para la semana y el calendario. */
export function dayLogOf(db: Db): Record<string, DayStatus> {
  const rows = [...(db.progress?.days ?? []), ...(db.today?.days ?? [])];
  return Object.fromEntries(rows.map((r) => [r.day, r.status]));
}

export const latestActiveSession = (db: Db): SessionInfo | undefined => {
  const s = db.today?.active_sessions[0];
  return s ? toInfo(s) : undefined;
};

export const pendingAnswers = (db: Db) => db.outbox.filter((o) => !o.writing || o.writing.mode === "recall").length;
