"use client";

import { Cloud, CloudOff, Loader2 } from "lucide-react";
import { useSyncExternalStore } from "react";
import { useT } from "@/lib/i18n";
import { useDb } from "@/lib/store/db";
import { pendingAnswers } from "@/lib/store/selectors";

function subscribeOnline(cb: () => void) {
  window.addEventListener("online", cb);
  window.addEventListener("offline", cb);
  return () => {
    window.removeEventListener("online", cb);
    window.removeEventListener("offline", cb);
  };
}

/** HU-E06-01: el estudiante ve que cada respuesta queda guardada, también sin red. */
export function SyncChip() {
  const { t } = useT();
  const db = useDb();
  const online = useSyncExternalStore(subscribeOnline, () => navigator.onLine, () => true);
  const pending = pendingAnswers(db);
  const state = !online && pending > 0 ? "offline" : pending > 0 ? "pending" : "saved";
  return (
    <span
      aria-live="polite"
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-bold ${state === "offline" ? "bg-hard-soft text-ink" : "text-ink-3"}`}
    >
      {state === "offline" ? <CloudOff className="size-3.5" aria-hidden /> : state === "pending" ? <Loader2 className="size-3.5 animate-spin" aria-hidden /> : <Cloud className="size-3.5" aria-hidden />}
      <span className={state === "offline" ? "" : "sr-only sm:not-sr-only"}>
        {state === "offline" ? t("session.sync.offline", { count: pending }) : state === "pending" ? t("session.sync.pending") : t("session.sync.saved")}
      </span>
    </span>
  );
}
