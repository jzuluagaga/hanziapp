"use client";

import { MailCheck } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { AuthShell } from "@/components/layout/auth-shell";
import { Button, ButtonLink } from "@/components/ui/button";
import { Field, inputClass } from "@/components/ui/primitives";
import { useT } from "@/lib/i18n";
import { confirmPasswordReset, requestPasswordReset } from "@/lib/store/actions";

export default function RecoverPage() {
  return (
    <Suspense>
      <Recover />
    </Suspense>
  );
}

/** HU-E02-02: recuperar la contraseña. El mensaje no revela si el correo existe (R-CTA-08). */
function Recover() {
  const params = useSearchParams();
  const uid = params.get("uid");
  const token = params.get("token");
  return uid && token ? <NewPassword uid={uid} token={token} /> : <RequestLink />;
}

function RequestLink() {
  const { t } = useT();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const valid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

  return (
    <AuthShell pose="durmiendo" title={t("auth.recover.title")} subtitle={sent ? undefined : t("auth.recover.body")}>
      {sent ? (
        <div className="space-y-6 text-center">
          <div className="flex items-start gap-3 rounded-[22px] bg-success-soft p-4 text-left">
            <MailCheck className="mt-0.5 size-5 shrink-0 text-success" aria-hidden />
            <p className="font-semibold">{t("auth.recover.sent")}</p>
          </div>
          <ButtonLink href="/login" block size="lg" variant="secondary">
            {t("auth.backToLogin")}
          </ButtonLink>
        </div>
      ) : (
        <form
          className="space-y-4"
          onSubmit={async (e) => {
            e.preventDefault();
            if (!valid) return;
            const r = await requestPasswordReset(email);
            if (r.ok) setSent(true);
            else setError(t(r.key === "rate_limited" ? "error.rate_limited" : r.key === "network" ? "error.network" : "error.generic"));
          }}
        >
          <Field label={t("auth.email")} htmlFor="email">
            <input id="email" type="email" autoComplete="email" required className={inputClass} value={email} onChange={(e) => setEmail(e.target.value)} />
          </Field>
          {error && (
            <p role="alert" className="rounded-2xl bg-error-soft px-4 py-3 text-sm font-semibold text-error">
              {error}
            </p>
          )}
          <Button type="submit" block size="lg" disabled={!valid}>
            {t("auth.recover.cta")}
          </Button>
          <ButtonLink href="/login" block variant="ghost">
            {t("auth.backToLogin")}
          </ButtonLink>
        </form>
      )}
    </AuthShell>
  );
}

function NewPassword({ uid, token }: { uid: string; token: string }) {
  const { t } = useT();
  const [password, setPassword] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <AuthShell pose="saluda" title={t("auth.reset.title")}>
      {done ? (
        <div className="space-y-6 text-center">
          <p className="rounded-[22px] bg-success-soft p-4 font-semibold">{t("auth.reset.done")}</p>
          <ButtonLink href="/login" block size="lg">
            {t("auth.backToLogin")}
          </ButtonLink>
        </div>
      ) : (
        <form
          className="space-y-4"
          onSubmit={async (e) => {
            e.preventDefault();
            const r = await confirmPasswordReset(uid, token, password);
            if (r.ok) setDone(true);
            else setError(t(r.key === "weak_password" ? "error.weak_password" : r.key === "reset_link_invalid" ? "error.reset_link_invalid" : "error.generic"));
          }}
        >
          <Field label={t("auth.password")} htmlFor="password" hint={t("auth.password.hint")}>
            <input id="password" type="password" autoComplete="new-password" required minLength={8} className={inputClass} value={password} onChange={(e) => setPassword(e.target.value)} />
          </Field>
          {error && (
            <p role="alert" className="rounded-2xl bg-error-soft px-4 py-3 text-sm font-semibold text-error">
              {error}
            </p>
          )}
          <Button type="submit" block size="lg" disabled={password.length < 8}>
            {t("auth.reset.cta")}
          </Button>
        </form>
      )}
    </AuthShell>
  );
}
