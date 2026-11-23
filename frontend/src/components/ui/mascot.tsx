"use client";

import Image from "next/image";
import { useT } from "@/lib/i18n";

export type MascotPose = "saluda" | "celebrando" | "durmiendo" | "triste";

export function Mascot({ pose = "saluda", size = 120, className = "", priority }: { pose?: MascotPose; size?: number; className?: string; priority?: boolean }) {
  const { t } = useT();
  return (
    <Image
      src={`/mascot/dragon-${pose}.png`}
      alt={t("a11y.mascot")}
      width={size}
      height={size}
      priority={priority}
      className={`select-none object-contain ${className}`}
      draggable={false}
    />
  );
}
