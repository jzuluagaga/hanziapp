"use client";

import { Eye, EyeOff } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AuthShell } from "@/components/layout/auth-shell";
import { Button } from "@/components/ui/button";
import { Field, inputClass } from "@/components/ui/primitives";
import { useT } from "@/lib/i18n";
import { loadMe, login } from "@/lib/store/actions";
import { useDb, useHydrated } from "@/lib/store/db";
import { isSignedIn } from "@/lib/store/selectors";

const KNOWN = ["invalid_credentials", "account_locked", "account_suspended", "rate_limited", "network"] as const;

/** HU-E02-02: entro, salgo y recupero el acceso sin ayuda. */
export default function LoginPage() {
  const { t } = useT();
  const router = useRouter();
  const db = useDb();
  const hydrated = useHydrated();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (hydrated && db.auth === "unknown") void loadMe();
    if (hydrated && isSignedIn(db)) router.replace("/today");
  }, [hydrated, db, router]);

  return (
    <AuthShell title={t("auth.login.title")} subtitle={t("auth.login.subtitle")}>
      <form
        className="space-y-4"
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          const r = await login(email, password);
          setBusy(false);
          if (r.ok) router.replace("/today");
          else setError(t(`error.${(KNOWN as readonly string[]).includes(r.key) ? r.key : "generic"}` as "error.generic"));
        }}
      >
        <Field label={t("auth.email")} htmlFor="email">
          <input id="email" type="email" autoComplete="email" required className={inputClass} value={email} onChange={(e) => setEmail(e.target.value)} />
        </Field>
        <Field label={t("auth.password")} htmlFor="password">
          <div className="relative">
            <input
              id="password"
              type={show ? "text" : "password"}
              autoComplete="current-password"
              required
              className={`${inputClass} pr-12`}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <button type="button" onClick={() => setShow((s) => !s)} aria-label={t("auth.showPassword")} aria-pressed={show} className="absolute right-2 top-1/2 grid size-9 -translate-y-1/2 place-items-center rounded-full text-ink-2 hover:bg-card">
              {show ? <EyeOff className="size-5" /> : <Eye className="size-5" />}
            </button>
          </div>
        </Field>
        {error && (
          <p role="alert" className="rounded-2xl bg-error-soft px-4 py-3 text-sm font-semibold text-error">
            {error}
          </p>
        )}
        <Button type="submit" block size="lg" disabled={busy}>
          {t("auth.login.cta")}
        </Button>
        <p className="flex flex-col items-center gap-2">
          <Link href="/recover-access" className="text-sm font-bold text-info hover:underline">
            {t("auth.login.forgot")}
          </Link>
          <Link href="/signup" className="text-sm font-bold text-primary hover:underline">
            {t("auth.login.noAccount")}
          </Link>
        </p>
      </form>

    </AuthShell>
  );
}
