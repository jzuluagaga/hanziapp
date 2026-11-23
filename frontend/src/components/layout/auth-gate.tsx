"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Mascot } from "@/components/ui/mascot";
import { useT } from "@/lib/i18n";
import { acceptPolicy, loadMe } from "@/lib/store/actions";
import { useDb, useHydrated } from "@/lib/store/db";

/** Muestra el contenido solo con acceso iniciado; si no, lleva a /login. */
export function AuthGate({ children }: { children: React.ReactNode }) {
  const hydrated = useHydrated();
  const db = useDb();
  const router = useRouter();

  useEffect(() => {
    if (hydrated && db.auth === "unknown") void loadMe();
  }, [hydrated, db.auth]);

  useEffect(() => {
    if (hydrated && db.auth === "signedOut") router.replace("/login");
  }, [hydrated, db.auth, router]);

  if (!hydrated || db.auth !== "signedIn" || !db.me) return <Splash />;
  if (db.me.policy.required) return <PolicyGate version={db.me.policy.current} />;
  return <>{children}</>;
}

/** R-DAT-01: una versión nueva de la política se acepta antes de continuar. */
function PolicyGate({ version }: { version: string }) {
  const { t } = useT();
  const [busy, setBusy] = useState(false);
  return (
    <div className="grid min-h-dvh place-items-center p-6">
      <div className="w-full max-w-md text-center">
        <Mascot pose="saluda" size={120} className="mx-auto" priority />
        <h1 className="mt-4 text-2xl font-black">{t("policy.required.title")}</h1>
        <p className="mt-2 text-ink-2">{t("policy.required.body", { version })}</p>
        <Link href="/data-policy" target="_blank" className="mt-4 inline-block font-bold text-info underline">
          {t("policy.required.read")}
        </Link>
        <Button
          block
          size="lg"
          className="mt-6"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            await acceptPolicy(version);
            setBusy(false);
          }}
        >
          {t("policy.required.accept")}
        </Button>
      </div>
    </div>
  );
}

export function Splash() {
  return (
    <div className="grid min-h-dvh place-items-center">
      <Mascot pose="saluda" size={96} className="animate-float opacity-90" priority />
    </div>
  );
}
