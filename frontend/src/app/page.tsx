import type { Metadata, Viewport } from "next";
import { Landing } from "@/components/landing/landing";

export const metadata: Metadata = {
  title: { absolute: "HanziApp · Aprender chino nunca fue tan fácil" },
  description:
    "Aprende el vocabulario del HSK leyendo, escuchando y escribiendo hanzi unos minutos al día, con repaso espaciado. Gratis para HSK 1 y 2.",
};

export const viewport: Viewport = { themeColor: "#F9F6F0" };

export default function Home() {
  return <Landing />;
}
