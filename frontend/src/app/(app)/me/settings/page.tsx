"use client";

import { FileText, Info, ShieldCheck, Trash2, UserRound } from "lucide-react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Badge, Container, ListRow, Segmented, SectionTitle, TopBar } from "@/components/ui/primitives";
import { config } from "@/lib/config";
import { useT } from "@/lib/i18n";
import { logout, updateProfile } from "@/lib/store/actions";
import { useDb } from "@/lib/store/db";
import { profileOf } from "@/lib/store/selectors";

export default function SettingsPage() {
  const db = useDb();
  const { t } = useT();
  const router = useRouter();
  const profile = profileOf(db);
  const icon = "size-5 text-ink-2";

  return (
    <div className="pb-28">
      <TopBar title={t("settings.title")} backHref="/me" />
      <Container>
        <div className="flex items-center justify-between gap-3 rounded-2xl bg-peach px-4 py-4">
          <div>
            <p className="text-xs font-extrabold uppercase tracking-wider text-ink-3">{t("settings.plan")}</p>
            <p className="font-bold">{db.me?.plan === "pro" ? t("common.plan.pro") : t("settings.plan.free")}</p>
          </div>
          <Badge tone="success">{db.me?.plan === "pro" ? t("common.plan.pro") : t("common.plan.free")}</Badge>
        </div>

        <div className="mt-4 space-y-2">
          <ListRow href="/me/settings/profile" leading={<UserRound className={icon} aria-hidden />}>
            {t("settings.profile")}
          </ListRow>
          <ListRow href="/me/settings/privacy" leading={<ShieldCheck className={icon} aria-hidden />}>
            {t("settings.privacy")}
          </ListRow>
          <ListRow href="/data-policy" leading={<FileText className={icon} aria-hidden />}>
            {t("settings.policy")}
          </ListRow>
          <ListRow href="/credits" leading={<Info className={icon} aria-hidden />}>
            {t("settings.credits")}
          </ListRow>
        </div>

        <SectionTitle>{t("settings.appearance")}</SectionTitle>
        <Segmented
          label={t("settings.appearance")}
          value={profile.theme}
          onChange={(theme) => updateProfile({ theme })}
          options={[
            { value: "system", label: t("settings.theme.system") },
            { value: "light", label: t("settings.theme.light") },
            { value: "dark", label: t("settings.theme.dark") },
          ]}
        />

        <div className="mt-8 space-y-2">
          <ListRow href="/me/settings/delete-account" danger leading={<Trash2 className="size-5" aria-hidden />}>
            {t("settings.deleteAccount")}
          </ListRow>
        </div>

        <div className="mt-10 text-center">
          <p className="text-sm font-bold">{t("settings.signedAs")}</p>
          <p className="text-ink-2">{db.me?.account.email}</p>
          <Button
            block
            size="lg"
            className="mt-4"
            onClick={async () => {
              await logout();
              router.replace("/login");
            }}
          >
            {t("settings.logout")}
          </Button>
          <p className="mt-3 text-xs font-bold text-ink-3">{t("settings.version", { version: config.appVersion })}</p>
        </div>
      </Container>
    </div>
  );
}
