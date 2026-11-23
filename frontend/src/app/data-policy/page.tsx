"use client";

import { Badge, Container, TopBar } from "@/components/ui/primitives";
import { config } from "@/lib/config";
import { useT } from "@/lib/i18n";

/** R-DAT-01: política versionada, disponible en cada idioma de interfaz activo. */
export default function DataPolicyPage() {
  const { t } = useT();
  const sections = [1, 2, 3, 4] as const;
  return (
    <div className="min-h-dvh pb-16">
      <TopBar title={t("policy.title")} />
      <Container>
        <Badge tone="info">{t("policy.version", { version: config.dataPolicyVersion })}</Badge>
        <p className="mt-3 rounded-2xl bg-hard-soft p-4 text-sm font-semibold text-ink-2">{t("policy.draftNotice")}</p>
        <div className="mt-6 space-y-6">
          {sections.map((n) => (
            <section key={n}>
              <h2 className="text-lg font-extrabold">{t(`policy.s${n}.title`)}</h2>
              <p className="mt-1 leading-relaxed text-ink-2">{t(`policy.s${n}.body`)}</p>
            </section>
          ))}
        </div>
      </Container>
    </div>
  );
}
