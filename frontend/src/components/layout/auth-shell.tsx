"use client";

import { Logo } from "@/components/ui/logo";
import { Mascot, type MascotPose } from "@/components/ui/mascot";
import { useT } from "@/lib/i18n";

/** Marco de las pantallas de acceso: cielo cálido arriba y tarjeta blanca. */
export function AuthShell({ pose = "saluda", title, subtitle, children }: { pose?: MascotPose; title: string; subtitle?: string; children: React.ReactNode }) {
  const { t } = useT();
  return (
    <div className="min-h-dvh">
      <div className="relative h-64 overflow-hidden" style={{ background: "linear-gradient(170deg, #E84C3D 0%, #F26B35 45%, #FF9F1C 100%)" }}>
        <div aria-hidden className="absolute -left-10 bottom-10 h-24 w-48 rounded-full bg-[var(--cloud)]" />
        <div aria-hidden className="absolute -right-12 bottom-16 h-24 w-52 rounded-full bg-[var(--cloud)]" />
        <div className="relative flex justify-center pt-[max(1rem,env(safe-area-inset-top))]">
          <Logo size={40} />
        </div>
      </div>
      <div className="dome relative -mt-24 bg-bg px-4 pb-12">
        <div className="mx-auto max-w-[420px]">
          <div className="-mt-20 flex justify-center">
            <Mascot pose={pose} size={150} priority className="animate-float drop-shadow-xl" />
          </div>
          <h1 className="mt-2 text-center text-[28px] font-black leading-tight">{title}</h1>
          {subtitle && <p className="mt-1 text-center text-ink-2">{subtitle}</p>}
          <div className="mt-6">{children}</div>
        </div>
      </div>
    </div>
  );
}
