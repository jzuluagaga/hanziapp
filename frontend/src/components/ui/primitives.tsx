"use client";

import { ChevronLeft, ChevronRight, X } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useId, useRef } from "react";
import { useT } from "@/lib/i18n";

/* ───────── Contenedor de página ───────── */
export function Container({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={`mx-auto w-full max-w-[640px] px-4 sm:px-6 ${className}`}>{children}</div>;
}

export function SectionTitle({ children, action }: { children: React.ReactNode; action?: React.ReactNode }) {
  return (
    <div className="mb-3 mt-8 flex items-end justify-between gap-4">
      <h2 className="text-[17px] font-extrabold tracking-tight text-ink">{children}</h2>
      {action}
    </div>
  );
}

/* ───────── Fila de lista (estilo Configuración de Headspace) ───────── */
export function ListRow({
  href,
  onClick,
  children,
  leading,
  trailing,
  danger,
}: {
  href?: string;
  onClick?: () => void;
  children: React.ReactNode;
  leading?: React.ReactNode;
  trailing?: React.ReactNode;
  danger?: boolean;
}) {
  const cls = `flex w-full items-center gap-3 rounded-2xl bg-surface px-4 py-4 text-left text-[15px] font-bold transition hover:brightness-[0.98] active:scale-[0.995] ${danger ? "text-error" : "text-ink"}`;
  const inner = (
    <>
      {leading}
      <span className="min-w-0 flex-1">{children}</span>
      {trailing ?? <ChevronRight className="size-5 shrink-0 text-ink" aria-hidden />}
    </>
  );
  if (href)
    return (
      <Link href={href} className={cls}>
        {inner}
      </Link>
    );
  return (
    <button type="button" onClick={onClick} className={cls}>
      {inner}
    </button>
  );
}

/* ───────── Barra superior de subpáginas ───────── */
export function TopBar({ title, backHref, right }: { title?: string; backHref?: string; right?: React.ReactNode }) {
  const router = useRouter();
  const { t } = useT();
  return (
    <div className="sticky top-0 z-30 bg-bg/90 backdrop-blur">
      <Container className="flex h-14 items-center gap-2">
        <button
          type="button"
          onClick={() => (backHref ? router.push(backHref) : router.back())}
          aria-label={t("common.back")}
          className="-ml-2 grid size-10 place-items-center rounded-full text-ink hover:bg-surface"
        >
          <ChevronLeft className="size-6" />
        </button>
        <h1 className="flex-1 truncate text-center text-base font-extrabold">{title}</h1>
        <div className="flex min-w-10 justify-end">{right}</div>
      </Container>
    </div>
  );
}

/* ───────── Insignias y barras ───────── */
type Tone = "neutral" | "success" | "hard" | "error" | "info" | "amber" | "primary";
const tones: Record<Tone, string> = {
  neutral: "bg-surface text-ink-2",
  success: "bg-success-soft text-success",
  hard: "bg-hard-soft text-[color-mix(in_srgb,var(--hard)_75%,var(--ink))]",
  error: "bg-error-soft text-error",
  info: "bg-info-soft text-info",
  amber: "bg-peach text-[color-mix(in_srgb,var(--amber)_70%,var(--ink))]",
  primary: "bg-primary text-on-color",
};
export function Badge({ tone = "neutral", children, className = "" }: { tone?: Tone; children: React.ReactNode; className?: string }) {
  return <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-bold ${tones[tone]} ${className}`}>{children}</span>;
}

export function ProgressBar({ value, max, tone = "amber", label }: { value: number; max: number; tone?: "amber" | "success" | "primary" | "info"; label?: string }) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  const color = { amber: "bg-amber", success: "bg-success", primary: "bg-primary", info: "bg-info" }[tone];
  return (
    <div className="h-2.5 w-full overflow-hidden rounded-full bg-surface" role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={max} aria-label={label}>
      <div className={`h-full rounded-full ${color} transition-[width] duration-500`} style={{ width: `${pct}%` }} />
    </div>
  );
}

/* ───────── Interruptor ───────── */
export function Switch({ checked, onChange, disabled, label }: { checked: boolean; onChange: (v: boolean) => void; disabled?: boolean; label: string }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`relative h-7 w-12 shrink-0 rounded-full transition-colors disabled:opacity-60 ${checked ? "bg-success" : "bg-border"}`}
    >
      <span className={`absolute top-0.5 size-6 rounded-full bg-white shadow transition-transform ${checked ? "translate-x-[22px]" : "translate-x-0.5"}`} />
    </button>
  );
}

/* ───────── Control segmentado ───────── */
export function Segmented<T extends string>({
  value,
  options,
  onChange,
  label,
}: {
  value: T;
  options: { value: T; label: React.ReactNode }[];
  onChange: (v: T) => void;
  label: string;
}) {
  return (
    <div role="radiogroup" aria-label={label} className="flex gap-1 rounded-full bg-surface p-1">
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          role="radio"
          aria-checked={value === o.value}
          onClick={() => onChange(o.value)}
          className={`flex-1 rounded-full px-3 py-2 text-sm font-bold transition ${value === o.value ? "bg-card text-ink shadow-soft" : "text-ink-2 hover:text-ink"}`}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

/* ───────── Hoja inferior / diálogo ───────── */
export function Sheet({ open, onClose, title, children }: { open: boolean; onClose: () => void; title: string; children: React.ReactNode }) {
  const { t } = useT();
  const id = useId();
  const panel = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const prev = document.activeElement as HTMLElement | null;
    panel.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = overflow;
      prev?.focus?.();
    };
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center" role="presentation">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-[2px]" onClick={onClose} aria-hidden />
      <div
        ref={panel}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby={id}
        className="animate-rise relative max-h-[90dvh] w-full max-w-[520px] overflow-y-auto rounded-t-[28px] bg-card p-6 pb-[max(1.5rem,env(safe-area-inset-bottom))] shadow-soft outline-none sm:rounded-[28px]"
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <h2 id={id} className="text-lg font-extrabold leading-tight">
            {title}
          </h2>
          <button type="button" onClick={onClose} aria-label={t("common.close")} className="-mr-2 -mt-1 grid size-9 place-items-center rounded-full text-ink-2 hover:bg-surface">
            <X className="size-5" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

/* ───────── Campo de formulario ───────── */
export function Field({ label, hint, error, children, htmlFor }: { label: string; hint?: string; error?: string; children: React.ReactNode; htmlFor: string }) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={htmlFor} className="block text-sm font-bold text-ink">
        {label}
      </label>
      {children}
      {error ? <p className="text-sm font-semibold text-error">{error}</p> : hint ? <p className="text-sm text-ink-2">{hint}</p> : null}
    </div>
  );
}

export const inputClass =
  "h-12 w-full rounded-2xl border-2 border-transparent bg-surface px-4 text-[15px] font-semibold text-ink placeholder:text-ink-3 placeholder:font-normal outline-none transition focus:border-info/50 focus:bg-card";

export function Checkbox({ checked, onChange, children, id }: { checked: boolean; onChange: (v: boolean) => void; children: React.ReactNode; id: string }) {
  return (
    <label htmlFor={id} className="flex cursor-pointer items-start gap-3 text-sm leading-snug text-ink">
      <input id={id} type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} className="mt-0.5 size-5 shrink-0 accent-[var(--primary)]" />
      <span>{children}</span>
    </label>
  );
}
