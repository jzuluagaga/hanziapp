"use client";

import { Users } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { AuthShell } from "@/components/layout/auth-shell";
import { Button } from "@/components/ui/button";
import { Checkbox, Field, inputClass } from "@/components/ui/primitives";
import { useT } from "@/lib/i18n";
import { loadConfig, register } from "@/lib/store/actions";
import { useDb } from "@/lib/store/db";

const KNOWN = ["email_taken", "weak_password", "signup_closed", "policy_not_accepted", "adult_required", "rate_limited", "network"] as const;

export default function SignupPage() {
  return (
    <Suspense>
      <Signup />
    </Suspense>
  );
}

/** HU-E02-01: me registro con correo aceptando la política (R-CTA-05, R-DAT-02, R-DAT-03). */
function Signup() {
  const { t } = useT();
  const router = useRouter();
  const cohort = useSearchParams().get("cohort") ?? undefined;
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [policy, setPolicy] = useState(false);
  const [adult, setAdult] = useState(false);
  const [reminder, setReminder] = useState(false); // opcional: nunca marcado por defecto
  const [submitted, setSubmitted] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const db = useDb();
  useEffect(() => {
    if (!db.config) void loadConfig();
  }, [db.config]);

  const errors = {
    name: !name.trim() ? t("auth.nameRequired") : undefined,
    email: !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) ? t("auth.invalidEmail") : undefined,
    password: password.length < 8 ? t("auth.shortPassword") : undefined,
    consent: !policy || !adult ? t("auth.signup.required") : undefined,
  };
  const valid = !errors.name && !errors.email && !errors.password && !errors.consent;

  return (
    <AuthShell pose="celebrando" title={t("auth.signup.title")} subtitle={t("auth.signup.subtitle")}>
      {cohort && (
        <p className="mb-4 flex items-center justify-center gap-2 rounded-2xl bg-info-soft px-4 py-3 text-sm font-bold text-info">
          <Users className="size-4" aria-hidden /> {t("auth.signup.cohort")}
        </p>
      )}
      <form
        noValidate
        className="space-y-4"
        onSubmit={async (e) => {
          e.preventDefault();
          setSubmitted(true);
          setServerError(null);
          if (!valid) return;
          setBusy(true);
          const policyVersion = db.config?.policy_version ?? (await loadConfig())?.policy_version ?? "";
          const r = await register({ name, email, password, cohort, reminderConsent: reminder, isAdult: adult, policyVersion });
          setBusy(false);
          if (r.ok) router.replace("/today");
          else setServerError(t(`error.${(KNOWN as readonly string[]).includes(r.key) ? r.key : "generic"}` as "error.generic"));
        }}
      >
        <Field label={t("auth.name")} htmlFor="name" error={submitted ? errors.name : undefined}>
          <input id="name" autoComplete="given-name" maxLength={60} className={inputClass} value={name} onChange={(e) => setName(e.target.value)} />
        </Field>
        <Field label={t("auth.email")} htmlFor="email" error={submitted ? errors.email : undefined}>
          <input id="email" type="email" autoComplete="email" className={inputClass} value={email} onChange={(e) => setEmail(e.target.value)} />
        </Field>
        <Field label={t("auth.password")} htmlFor="password" hint={t("auth.password.hint")} error={submitted ? errors.password : undefined}>
          <input id="password" type="password" autoComplete="new-password" className={inputClass} value={password} onChange={(e) => setPassword(e.target.value)} />
        </Field>

        <div className="space-y-3 rounded-[22px] bg-surface p-4">
          <Checkbox id="policy" checked={policy} onChange={setPolicy}>
            {t("auth.signup.policy.pre")}{" "}
            <Link href="/data-policy" target="_blank" className="font-bold text-info underline">
              {t("auth.signup.policy.link")}
            </Link>
          </Checkbox>
          <Checkbox id="adult" checked={adult} onChange={setAdult}>
            {t("auth.signup.age")}
          </Checkbox>
          <div className="h-px bg-border" />
          <Checkbox id="reminder" checked={reminder} onChange={setReminder}>
            {t("auth.signup.reminder")} <span className="text-ink-3">({t("common.optional").toLowerCase()})</span>
          </Checkbox>
        </div>
        {submitted && errors.consent && (
          <p role="alert" className="rounded-2xl bg-error-soft px-4 py-3 text-sm font-semibold text-error">
            {errors.consent}
          </p>
        )}

        {serverError && (
          <p role="alert" className="rounded-2xl bg-error-soft px-4 py-3 text-sm font-semibold text-error">
            {serverError}
          </p>
        )}
        <Button type="submit" block size="lg" disabled={busy}>
          {t("auth.signup.cta")}
        </Button>
        <p className="text-center">
          <Link href="/login" className="text-sm font-bold text-info hover:underline">
            {t("auth.signup.haveAccount")}
          </Link>
        </p>
      </form>
    </AuthShell>
  );
}
