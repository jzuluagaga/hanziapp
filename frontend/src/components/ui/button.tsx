import Link from "next/link";
import { forwardRef } from "react";

type Variant = "primary" | "secondary" | "ghost" | "success" | "fail" | "outline" | "danger";
type Size = "md" | "lg" | "sm";

const base =
  "inline-flex items-center justify-center gap-2 rounded-full font-bold transition-[background,transform,box-shadow] duration-150 active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none select-none";

const variants: Record<Variant, string> = {
  primary: "bg-primary text-on-color hover:bg-primary-hover shadow-[0_4px_0_0_var(--primary-hover)] active:shadow-none active:translate-y-[2px]",
  secondary: "bg-surface text-ink hover:brightness-[0.97]",
  ghost: "text-ink-2 hover:bg-surface",
  success: "bg-success text-on-color hover:brightness-95 shadow-[0_4px_0_0_color-mix(in_srgb,var(--success)_70%,black)] active:shadow-none active:translate-y-[2px]",
  fail: "bg-error-soft text-error hover:brightness-[0.97] border-2 border-error/25",
  outline: "border-2 border-border text-ink hover:bg-surface",
  danger: "bg-error text-on-color hover:brightness-95",
};

const sizes: Record<Size, string> = {
  sm: "h-9 px-4 text-sm",
  md: "h-12 px-6 text-[15px]",
  lg: "h-14 px-7 text-base",
};

export function buttonClass(variant: Variant = "primary", size: Size = "md", extra = "") {
  return `${base} ${variants[variant]} ${sizes[size]} ${extra}`;
}

type BtnProps = React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; size?: Size; block?: boolean };

export const Button = forwardRef<HTMLButtonElement, BtnProps>(function Button(
  { variant = "primary", size = "md", block, className = "", type = "button", ...rest },
  ref,
) {
  return <button ref={ref} type={type} className={buttonClass(variant, size, `${block ? "w-full" : ""} ${className}`)} {...rest} />;
});

export function ButtonLink({
  href,
  variant = "primary",
  size = "md",
  block,
  className = "",
  children,
}: {
  href: string;
  variant?: Variant;
  size?: Size;
  block?: boolean;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <Link href={href} className={buttonClass(variant, size, `${block ? "w-full" : ""} ${className}`)}>
      {children}
    </Link>
  );
}
