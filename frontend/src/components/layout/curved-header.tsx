import { Container } from "@/components/ui/primitives";

export type HeaderVariant = "sunrise" | "amber" | "info" | "rays" | "coral" | "jade" | "peach";

const backgrounds: Record<HeaderVariant, string> = {
  sunrise: "linear-gradient(170deg, #E84C3D 0%, #F26B35 45%, #FF9F1C 100%)",
  amber: "linear-gradient(180deg, #FF9F1C 0%, #FFAE3F 100%)",
  info: "linear-gradient(180deg, #4A90E2 0%, #5D9DE6 100%)",
  coral: "linear-gradient(180deg, #E84C3D 0%, #EC5E4F 100%)",
  jade: "linear-gradient(180deg, #2A9D8F 0%, #36AC9E 100%)",
  peach: "linear-gradient(180deg, #F4A261 0%, #F7B27A 100%)",
  rays: "radial-gradient(circle at 50% 135%, #FF9F1C 0 34%, #FCA03A 34% 42%, #F7863A 42% 52%, #F06A3A 52% 62%, #E84C3D 62% 74%, #D13B2D 74%)",
};

export function Clouds({ puffs = true }: { puffs?: boolean }) {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0">
      <div className="absolute -left-12 -bottom-2 h-16 w-44 rounded-full bg-[var(--cloud)]" />
      <div className="absolute -right-14 bottom-0 h-20 w-52 rounded-full bg-[var(--cloud)]" />
      {puffs && (
        <>
          <div className="absolute right-[34%] top-5 h-5 w-16 rounded-full bg-white/30" />
          <div className="absolute right-[30%] top-3 h-7 w-10 rounded-full bg-white/30" />
          <div className="absolute left-[8%] top-3 h-4 w-12 rounded-full bg-white/25" />
        </>
      )}
    </div>
  );
}

/**
 * Encabezado de color con el contenido que "sube" en curva sobre él,
 * como las secciones de Headspace. El contenido de la página va en `children`.
 */
export function CurvedPage({
  variant,
  header,
  children,
  clouds,
  headerClassName = "",
}: {
  variant: HeaderVariant;
  header: React.ReactNode;
  children: React.ReactNode;
  clouds?: boolean;
  headerClassName?: string;
}) {
  return (
    <>
      <header className={`relative overflow-hidden text-white ${headerClassName}`} style={{ background: backgrounds[variant] }}>
        {clouds && <Clouds />}
        <Container className="relative pb-16 pt-[max(1rem,env(safe-area-inset-top))]">{header}</Container>
      </header>
      <main className="dome relative -mt-10 min-h-[60dvh] bg-bg pb-28 pt-6">
        <Container>{children}</Container>
      </main>
    </>
  );
}

export const levelVariant: Record<number, HeaderVariant> = { 1: "coral", 2: "amber", 3: "jade", 4: "info", 5: "peach", 6: "sunrise" };
export const levelColor: Record<number, string> = { 1: "#E84C3D", 2: "#FF9F1C", 3: "#2A9D8F", 4: "#4A90E2", 5: "#F4A261", 6: "#D13B2D" };
