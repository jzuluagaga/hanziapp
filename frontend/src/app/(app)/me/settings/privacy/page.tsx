"use client";

import { ChevronRight } from "lucide-react";
import Link from "next/link";
import { Container, SectionTitle, Switch, TopBar } from "@/components/ui/primitives";
import { useToast } from "@/components/ui/toast";
import { useT } from "@/lib/i18n";
import { setConsent } from "@/lib/store/actions";
import { useDb } from "@/lib/store/db";

/** HU-E10-02: leo la política y doy o retiro cada consentimiento (R-DAT-01, R-DAT-02). */
export default function PrivacyPage() {
  const db = useDb();
  const { t, lang } = useT();
  const toast = useToast();
  const reminder = db.me?.consents.reminder_email ?? false;
  const policy = db.me?.policy;
  const accepted = policy?.accepted && policy.accepted_at ? { version: policy.accepted, at: policy.accepted_at } : null;
  const date = accepted ? new Intl.DateTimeFormat(lang, { dateStyle: "long" }).format(new Date(accepted.at)) : "";

  return (
    <div className="pb-28">
      <TopBar title={t("privacy.title")} backHref="/me/settings" />
      <Container>
        {accepted && (
          <Link href="/data-policy" className="flex items-center gap-3 rounded-[22px] bg-info-soft p-4 transition hover:brightness-[0.98]">
            <span className="min-w-0 flex-1">
              <span className="block text-sm text-ink-2">{t("privacy.policy.accepted", { version: accepted.version, date })}</span>
              <span className="mt-1 block font-extrabold text-info">{t("privacy.policy.read")}</span>
            </span>
            <ChevronRight className="size-5 text-info" aria-hidden />
          </Link>
        )}

        <SectionTitle>{t("privacy.consents")}</SectionTitle>
        <ul className="space-y-2">
          <li className="flex items-center gap-4 rounded-[22px] bg-surface p-4">
            <span className="min-w-0 flex-1">
              <span className="block font-bold">{t("privacy.consent.general")}</span>
              <span className="block text-sm text-ink-2">{t("privacy.consent.general.desc")}</span>
            </span>
            <Switch checked disabled onChange={() => {}} label={t("privacy.consent.general")} />
          </li>
          <li className="flex items-center gap-4 rounded-[22px] bg-surface p-4">
            <span className="min-w-0 flex-1">
              <span className="block font-bold">{t("privacy.consent.reminder")}</span>
              <span className="block text-sm text-ink-2">{t("privacy.consent.reminder.desc")}</span>
            </span>
            <Switch
              checked={reminder}
              onChange={async (v) => {
                const r = await setConsent("reminder_email", v);
                toast(r.ok ? t("privacy.consent.updated") : t("error.generic"));
              }}
              label={t("privacy.consent.reminder")}
            />
          </li>
        </ul>

        <SectionTitle>{t("privacy.rights")}</SectionTitle>
        <p className="rounded-[22px] bg-surface p-4 text-[15px] leading-relaxed text-ink-2">{t("privacy.rights.body")}</p>
      </Container>
    </div>
  );
}
