"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Mascot } from "@/components/ui/mascot";
import { Checkbox, Container, Field, inputClass, TopBar } from "@/components/ui/primitives";
import { useT } from "@/lib/i18n";
import { deleteAccount } from "@/lib/store/actions";

/** HU-E10-03 / R-DAT-06: borrado definitivo de la cuenta y sus datos. */
export default function DeleteAccountPage() {
  const { t } = useT();
  const router = useRouter();
  const [confirmed, setConfirmed] = useState(false);
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  return (
    <div className="pb-28">
      <TopBar title={t("delete.title")} backHref="/me/settings" />
      <Container>
        <div className="flex flex-col items-center text-center">
          <Mascot pose="triste" size={170} />
          <p className="mt-2 text-lg font-extrabold">{t("delete.lead")}</p>
        </div>
        <ul className="mt-5 space-y-2">
          {(["delete.item.profile", "delete.item.progress", "delete.item.consents"] as const).map((k) => (
            <li key={k} className="flex items-center gap-3 rounded-2xl bg-error-soft px-4 py-3 font-semibold">
              <span className="size-2 shrink-0 rounded-full bg-error" />
              {t(k)}
            </li>
          ))}
        </ul>
        <p className="mt-4 text-center font-extrabold text-error">{t("delete.irreversible")}</p>
        <div className="mt-6 rounded-2xl bg-surface p-4">
          <Checkbox id="confirm-delete" checked={confirmed} onChange={setConfirmed}>
            {t("delete.confirm")}
          </Checkbox>
        </div>
        <div className="mt-4">
          <Field label={t("delete.password")} htmlFor="delete-password">
            <input id="delete-password" type="password" autoComplete="current-password" className={inputClass} value={password} onChange={(e) => setPassword(e.target.value)} />
          </Field>
        </div>
        {error && (
          <p role="alert" className="mt-3 rounded-2xl bg-error-soft px-4 py-3 text-sm font-semibold text-error">
            {error}
          </p>
        )}
        <Button
          variant="danger"
          block
          size="lg"
          className="mt-4"
          disabled={!confirmed || !password || busy}
          onClick={async () => {
            setBusy(true);
            const r = await deleteAccount(password);
            setBusy(false);
            if (r.ok) router.replace("/login");
            else setError(t(r.key === "invalid_credentials" ? "error.invalid_credentials" : r.key === "network" ? "error.network" : "error.generic"));
          }}
        >
          {t("delete.cta")}
        </Button>
      </Container>
    </div>
  );
}
