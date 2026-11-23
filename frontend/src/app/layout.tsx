import type { Metadata, Viewport } from "next";
import { Noto_Sans_SC, Nunito } from "next/font/google";
import { Providers } from "@/components/providers";
import "./globals.css";

const nunito = Nunito({ subsets: ["latin", "latin-ext"], variable: "--font-nunito", display: "swap" });
const notoSc = Noto_Sans_SC({ weight: ["400", "500", "700"], variable: "--font-noto-sc", display: "swap", preload: false });

export const metadata: Metadata = {
  title: { default: "HanziApp", template: "%s · HanziApp" },
  description: "Aprende hanzi un poco cada día, con repaso espaciado.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#F9F6F0" },
    { media: "(prefers-color-scheme: dark)", color: "#1C1A17" },
  ],
};

/** Aplica el tema guardado antes de pintar para evitar el destello. */
const themeScript = `try{var d=JSON.parse(localStorage.getItem("hanziapp.db.v1")||"{}");var t=d&&d.profile&&d.profile.theme;if(t==="light"||t==="dark")document.documentElement.dataset.theme=t;}catch(e){}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className={`${nunito.variable} ${notoSc.variable}`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="min-h-dvh">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
