"use client";

/**
 * Reproduce el audio de contenido: un archivo por texto, idioma y voz (R-CON-13,
 * R-IDI-08). En desarrollo, una dirección `tts:` indica que no hay archivo y se usa
 * la síntesis del navegador (Docs/10-api.md §5).
 */
let current: HTMLAudioElement | null = null;

export function speak(text: string, opts: { rate?: number; onEnd?: () => void } = {}): boolean {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return false;
  const synth = window.speechSynthesis;
  synth.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "zh-CN";
  u.rate = opts.rate ?? 0.85;
  const voice = synth.getVoices().find((v) => v.lang.toLowerCase().startsWith("zh"));
  if (voice) u.voice = voice;
  if (opts.onEnd) u.onend = opts.onEnd;
  synth.speak(u);
  return true;
}

/** Devuelve una promesa que se resuelve al terminar, o se rechaza si el audio no carga. */
export function play(src: string | null | undefined, text: string, onEnd?: () => void): Promise<void> {
  stopSpeaking();
  if (!src) return Promise.reject(new Error("no_audio"));
  if (src.startsWith("tts:")) {
    return speak(src.slice(4) || text, { onEnd }) ? Promise.resolve() : Promise.reject(new Error("tts_unavailable"));
  }
  const audio = new Audio(src);
  current = audio;
  if (onEnd) audio.onended = onEnd;
  return audio.play();
}

export function stopSpeaking() {
  if (typeof window !== "undefined" && "speechSynthesis" in window) window.speechSynthesis.cancel();
  current?.pause();
  current = null;
}
