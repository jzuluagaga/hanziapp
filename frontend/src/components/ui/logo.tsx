"use client";

import Image from "next/image";
import Link from "next/link";
import { useT } from "@/lib/i18n";

/** Marca de HanziApp: cabeza del dragón en círculo + nombre. */
export function Logo({ size = 48, tone = "light", href = "/" }: { size?: number; tone?: "light" | "dark"; href?: string }) {
  const { t } = useT();
  return (
    <Link href={href} className="group flex items-center gap-2.5 rounded-full pr-2" aria-label={t("app.name")}>
      <span
        className="relative shrink-0 overflow-hidden rounded-full bg-white shadow-[0_4px_14px_rgba(0,0,0,0.18)] ring-[3px] ring-white transition group-hover:scale-105"
        style={{ width: size, height: size }}
      >
        <Image src="/logo-mark.png" alt="" width={size * 2} height={size * 2} priority className="size-full object-cover" />
      </span>
      <span className={`text-lg font-black tracking-tight sm:text-[22px] ${tone === "light" ? "text-white [text-shadow:0_1px_8px_rgba(0,0,0,0.15)]" : "text-ink"}`}>
        {t("app.name")}
      </span>
    </Link>
  );
}
