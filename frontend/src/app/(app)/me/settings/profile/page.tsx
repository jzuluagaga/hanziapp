"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Container, Field, inputClass, SectionTitle, TopBar } from "@/components/ui/primitives";
import { useToast } from "@/components/ui/toast";
import { config } from "@/lib/config";
import type { LangCode, Profile } from "@/lib/domain/types";
import { useT } from "@/lib/i18n";
import { TIMEZONES } from "@/lib/timezones";
import { updateProfile } from "@/lib/store/actions";
import { useDb } from "@/lib/store/db";
import { profileOf } from "@/lib/store/selectors";

/** HU-E10-01: cambio nombre, idiomas, zona horaria y límites diarios. */
export default function ProfilePage() {
  const db = useDb();
  const { t } = useT();
  const toast = useToast();
  const [draft, setDraft] = useState<Profile>(profileOf(db));
  const set = <K extends keyof Profile>(k: K, v: Profile[K]) => setDraft((d) => ({ ...d, [k]: v }));
  const languages = db.config?.languages ?? [{ code: "es", is_study_active: true, is_ui_active: true }];
  const uiLangs = languages.filter((l) => l.is_ui_active);
  const studyLangs = languages.filter((l) => l.is_study_active);
  const limits = db.config?.limits;
  const [busy, setBusy] = useState(false);

  return (
    <div className="pb-28">
      <TopBar title={t("profile.title")} backHref="/me/settings" />
      <Container>
        <form
          className="space-y-5"
          onSubmit={async (e) => {
            e.preventDefault();
            if (!draft.name.trim()) return;
            setBusy(true);
            const r = await updateProfile({ ...draft, name: draft.name.trim() });
            setBusy(false);
            toast(r.ok ? t("common.saved") : t(`error.${["limit_out_of_range", "language_inactive", "timezone_invalid", "network"].includes(r.key) ? r.key : "generic"}` as "error.generic"));
          }}
        >
          <Field label={t("profile.name")} htmlFor="name" error={!draft.name.trim() ? t("auth.nameRequired") : undefined}>
            <input id="name" className={inputClass} value={draft.name} maxLength={60} onChange={(e) => set("name", e.target.value)} />
          </Field>

          <Field label={t("profile.uiLanguage")} htmlFor="ui-lang">
            <select id="ui-lang" className={inputClass} value={draft.uiLanguage} onChange={(e) => set("uiLanguage", e.target.value as LangCode)}>
              {uiLangs.map((l) => (
                <option key={l.code} value={l.code}>
                  {t(`lang.${l.code}` as "lang.es")}
                </option>
              ))}
            </select>
          </Field>

          <Field label={t("profile.studyLanguage")} htmlFor="study-lang" hint={t("profile.studyLanguage.hint")}>
            <select id="study-lang" className={inputClass} value={draft.studyLanguage} onChange={(e) => set("studyLanguage", e.target.value as LangCode)}>
              {studyLangs.map((l) => (
                <option key={l.code} value={l.code}>
                  {t(`lang.${l.code}` as "lang.es")}
                </option>
              ))}
            </select>
          </Field>

          <Field label={t("profile.timezone")} htmlFor="tz" hint={t("profile.timezone.hint")}>
            <select id="tz" className={inputClass} value={draft.timezone} onChange={(e) => set("timezone", e.target.value)}>
              {TIMEZONES.map((z) => (
                <option key={z} value={z}>
                  {z.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </Field>

          <SectionTitle>{t("profile.limits")}</SectionTitle>
          <div className="space-y-5 rounded-[22px] bg-surface p-5">
            <LimitSlider
              id="lim-rec"
              label={t("profile.limit.recognition")}
              value={draft.newLimitRecognition}
              min={limits?.new_limit_recognition.min ?? config.newLimitRecognition.min}
              max={limits?.new_limit_recognition.max ?? config.newLimitRecognition.max}
              onChange={(v) => set("newLimitRecognition", v)}
            />
            <LimitSlider
              id="lim-wri"
              label={t("profile.limit.writing")}
              value={draft.newLimitWriting}
              min={limits?.new_limit_writing.min ?? config.newLimitWriting.min}
              max={limits?.new_limit_writing.max ?? config.newLimitWriting.max}
              onChange={(v) => set("newLimitWriting", v)}
            />
            <p className="text-sm text-ink-2">{t("profile.limit.hint")}</p>
          </div>

          <Button type="submit" block size="lg" disabled={busy}>
            {t("common.save")}
          </Button>
        </form>
      </Container>
    </div>
  );
}

function LimitSlider({ id, label, value, min, max, onChange }: { id: string; label: string; value: number; min: number; max: number; onChange: (v: number) => void }) {
  const { t } = useT();
  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <label htmlFor={id} className="font-bold">
          {label}
        </label>
        <span className="rounded-full bg-card px-3 py-1 text-sm font-extrabold">{t("profile.limit.value", { count: value })}</span>
      </div>
      <input id={id} type="range" min={min} max={max} value={value} onChange={(e) => onChange(Number(e.target.value))} className="w-full accent-[var(--primary)]" />
    </div>
  );
}
