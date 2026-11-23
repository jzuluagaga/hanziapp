"use client";

import { Volume2 } from "lucide-react";
import { useState } from "react";
import { play } from "@/lib/audio";
import { useT } from "@/lib/i18n";
import { track } from "@/lib/store/actions";
import { useToast } from "@/components/ui/toast";

/** HU-E04-01: el audio suena cuando el estudiante lo pide; si no carga, se avisa sin bloquear. */
export function AudioButton({
  src,
  text,
  context = "card",
  target = "word",
  size = "md",
  className = "",
}: {
  src?: string | null;
  text: string;
  context?: "card" | "word_page";
  target?: "word" | "example";
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  const { t } = useT();
  const toast = useToast();
  const [playing, setPlaying] = useState(false);
  const dims = { sm: "size-8", md: "size-11", lg: "size-16" }[size];
  const icon = { sm: "size-4", md: "size-5", lg: "size-7" }[size];
  return (
    <button
      type="button"
      aria-label={t("a11y.playAudio")}
      onClick={(e) => {
        e.stopPropagation();
        setPlaying(true);
        play(src, text, () => setPlaying(false))
          .then(() => track("audio_played", { context, target, auto: false }))
          .catch(() => {
            setPlaying(false);
            toast(t("audio.unavailable"));
            track("audio_failed", { context, target });
          });
        setTimeout(() => setPlaying(false), 2500);
      }}
      className={`grid ${dims} shrink-0 place-items-center rounded-full bg-info text-on-color transition hover:brightness-95 active:scale-95 ${playing ? "ring-4 ring-info/25" : ""} ${className}`}
    >
      <Volume2 className={icon} aria-hidden />
    </button>
  );
}
