import type { Metadata } from "next";

// R-CTA-10: registro abierto por una dirección no publicada; los buscadores no la indexan.
export const metadata: Metadata = { robots: { index: false, follow: false } };

export default function SignupLayout({ children }: { children: React.ReactNode }) {
  return children;
}
