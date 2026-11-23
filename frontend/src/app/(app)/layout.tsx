import { AuthGate } from "@/components/layout/auth-gate";
import { TabBar } from "@/components/layout/tab-bar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGate>
      {children}
      <TabBar />
    </AuthGate>
  );
}
