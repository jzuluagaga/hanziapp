"use client";

import { RotateCcw } from "lucide-react";
import { useEffect, useRef } from "react";
import type HanziWriter from "hanzi-writer";
import { useT } from "@/lib/i18n";
import { track } from "@/lib/store/actions";
import { CharGrid } from "./char-grid";

/** HU-E07-03: animación del orden de trazos. */
export function StrokeAnimation({ char, size = 132 }: { char: string; size?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const writer = useRef<HanziWriter | null>(null);
  const { t } = useT();

  useEffect(() => {
    let cancelled = false;
    const el = ref.current;
    if (!el) return;
    import("hanzi-writer").then(({ default: HW }) => {
      if (cancelled) return;
      el.innerHTML = "";
      const styles = getComputedStyle(document.documentElement);
      writer.current = HW.create(el, char, {
        width: size,
        height: size,
        padding: 8,
        strokeColor: styles.getPropertyValue("--ink").trim() || "#2D2A26",
        radicalColor: "#E84C3D",
        outlineColor: styles.getPropertyValue("--border").trim() || "#E6E0D6",
        strokeAnimationSpeed: 1.2,
        delayBetweenStrokes: 180,
        showCharacter: false,
      });
      writer.current.animateCharacter();
      track("stroke_order_played");
    });
    return () => {
      cancelled = true;
      writer.current = null;
    };
  }, [char, size]);

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative rounded-2xl bg-card" style={{ width: size, height: size }}>
        <CharGrid />
        <div ref={ref} className="relative" />
      </div>
      <button
        type="button"
        onClick={() => {
          writer.current?.animateCharacter();
          track("stroke_order_played");
        }}
        className="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold text-ink-2 hover:bg-surface"
        aria-label={`${t("word.strokes.replay")} ${char}`}
      >
        <RotateCcw className="size-3.5" aria-hidden /> {t("word.strokes.replay")}
      </button>
    </div>
  );
}
