import { config } from "@/lib/config";

/**
 * Día local del estudiante (R-PRO-01): según su zona horaria y con corte a las
 * `dayRolloverHour`:00. Una respuesta a la 1:30 a. m. pertenece al día anterior.
 */
export function localDay(date: Date, timezone: string): string {
  const shifted = new Date(date.getTime() - config.dayRolloverHour * 3600_000);
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: timezone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(shifted);
  return parts; // en-CA → YYYY-MM-DD
}

export function addDays(day: string, n: number): string {
  const d = new Date(`${day}T12:00:00Z`);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}

export function diffDays(a: string, b: string): number {
  return Math.round((new Date(`${a}T12:00:00Z`).getTime() - new Date(`${b}T12:00:00Z`).getTime()) / 86_400_000);
}

/** 0 = lunes … 6 = domingo */
export function weekdayIndex(day: string): number {
  return (new Date(`${day}T12:00:00Z`).getUTCDay() + 6) % 7;
}

export function hourIn(timezone: string, date = new Date()): number {
  return Number(new Intl.DateTimeFormat("en-GB", { timeZone: timezone, hour: "2-digit", hour12: false }).format(date));
}
