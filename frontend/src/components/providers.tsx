"use client";

import { useEffect } from "react";
import { clearNotice, flush, loadConfig, scheduleFlush } from "@/lib/store/actions";
import { useDb, useHydrated } from "@/lib/store/db";
import { useT } from "@/lib/i18n";
import { ToastProvider, useToast } from "./ui/toast";

export function Providers({ children }: { children: React.ReactNode }) {
  const db = useDb();
  const hydrated = useHydrated();
  const theme = db.me?.profile.theme ?? "system";
  const lang = db.me?.profile.ui_language ?? "es";

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "system") delete root.dataset.theme;
    else root.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  useEffect(() => {
    if (!hydrated) return;
    void loadConfig();
    // R-SES-04: lo que quedó en el buzón se reenvía solo al abrir y al volver la red.
    void flush();
    const onOnline = () => scheduleFlush(0);
    window.addEventListener("online", onOnline);
    return () => window.removeEventListener("online", onOnline);
  }, [hydrated]);

  return (
    <ToastProvider>
      <Notices />
      {children}
    </ToastProvider>
  );
}

/** Avisos que nacen fuera de una pantalla (R-SES-07: la sesión avanzó en otro dispositivo). */
function Notices() {
  const db = useDb();
  const toast = useToast();
  const { t } = useT();
  useEffect(() => {
    if (db.notice === "relocated") {
      toast(t("session.relocated"));
      clearNotice();
    }
  }, [db.notice, toast, t]);
  return null;
}
