"use client";

import { Container, TopBar } from "@/components/ui/primitives";
import { Mascot } from "@/components/ui/mascot";
import { useT, type Key } from "@/lib/i18n";

/** R-CON-15: página de créditos con licencias de datos y librerías. */
const ITEMS: Key[] = ["credits.syllabus", "credits.strokes", "credits.hanziWriter", "credits.fonts", "credits.icons", "credits.framework"];

export default function CreditsPage() {
  const { t } = useT();
  return (
    <div className="min-h-dvh pb-16">
      <TopBar title={t("credits.title")} />
      <Container>
        <div className="flex flex-col items-center text-center">
          <Mascot pose="celebrando" size={130} />
          <p className="mt-2 max-w-sm text-ink-2">{t("credits.lead")}</p>
        </div>
        <ul className="mt-6 space-y-2">
          {ITEMS.map((k) => (
            <li key={k} className="rounded-2xl bg-surface px-4 py-3.5 text-[15px] font-semibold">
              {t(k)}
            </li>
          ))}
        </ul>
      </Container>
    </div>
  );
}
