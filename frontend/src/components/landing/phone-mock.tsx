"use client";

import { Cloud, Flame, Volume2, X } from "lucide-react";
import { Mascot } from "@/components/ui/mascot";
import { useT } from "@/lib/i18n";

/** Vista previa ilustrativa de una tarjeta de lectura, construida con los mismos estilos de la app. */
export function PhoneMock() {
  const { t } = useT();
  return (
    <div role="img" aria-label={t("landing.mock.label")} className="relative mx-auto w-[270px] text-ink sm:w-[290px]">
      <Mascot pose="saluda" size={140} className="absolute -bottom-10 -left-32 z-20 hidden drop-shadow-xl sm:block" />

      <div aria-hidden className="absolute -right-8 top-20 z-20 flex items-center gap-2 rounded-2xl bg-card px-3 py-2 text-sm font-extrabold text-ink shadow-soft">
        <span className="grid size-7 place-items-center rounded-lg bg-amber text-white">
          <Flame className="size-4" />
        </span>
        {t("landing.mock.streak")}
      </div>
      <div aria-hidden className="absolute -left-6 top-6 z-20 flex items-center gap-1.5 rounded-full bg-card px-3 py-1.5 text-xs font-bold text-success shadow-soft sm:-left-10">
        <Cloud className="size-3.5" />
        {t("landing.mock.saved")}
      </div>

      <div aria-hidden className="relative rotate-[2.5deg] rounded-[46px] bg-[#2D2A26] p-3 shadow-[0_30px_60px_-15px_rgba(45,42,38,0.45)]">
        <div className="flex h-[540px] flex-col overflow-hidden rounded-[36px] bg-bg p-4 sm:h-[570px]">
          <div className="flex items-center gap-2.5 pt-1">
            <X className="size-5 text-ink-2" />
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-surface">
              <div className="h-full w-3/5 rounded-full bg-amber" />
            </div>
            <span className="text-[10px] font-extrabold text-ink-2">{t("session.progress", { done: 6, total: 10 })}</span>
          </div>

          <div className="mt-4 flex flex-1 flex-col rounded-[26px] bg-card p-5 shadow-soft">
            <span className="w-fit rounded-full bg-surface px-2.5 py-0.5 text-[10px] font-bold text-ink-2">{t("common.level", { level: 1 })}</span>
            <div className="flex flex-1 flex-col items-center justify-center text-center">
              <p lang="zh-CN" className="font-hanzi text-[64px] leading-none text-ink">
                朋友
              </p>
              <div className="mt-4 flex items-center gap-2">
                <span lang="zh-Latn-pinyin" className="text-lg font-bold text-ink-2">péngyou</span>
                <span className="grid size-8 place-items-center rounded-full bg-info text-white">
                  <Volume2 className="size-4" />
                </span>
              </div>
              <div className="my-4 h-px w-full bg-border" />
              <p className="text-[11px] font-extrabold uppercase tracking-wider text-ink-3">{t("session.meanings")}</p>
              <p className="mt-1 text-lg font-extrabold">{t("landing.mock.meaning")}</p>
              <div className="mt-4 w-full rounded-2xl bg-surface p-3 text-left">
                <p lang="zh-CN" className="font-hanzi text-sm">他是我的好朋友。</p>
                <p lang="zh-Latn-pinyin" className="text-[11px] text-ink-2">Tā shì wǒ de hǎo péngyou.</p>
              </div>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-2 gap-2.5">
            <span className="grid h-11 place-items-center rounded-full border-2 border-error/25 bg-error-soft text-xs font-bold text-error">{t("session.fail")}</span>
            <span className="grid h-11 place-items-center rounded-full bg-success text-xs font-bold text-white shadow-[0_3px_0_0_color-mix(in_srgb,var(--success)_70%,black)]">
              {t("session.pass")}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
