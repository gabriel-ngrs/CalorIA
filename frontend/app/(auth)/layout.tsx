import { AuthLeftPanel } from "@/components/auth/AuthLeftPanel";
import { AuthRightPanel } from "@/components/auth/AuthRightPanel";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex">
      <AuthLeftPanel />
      <AuthRightPanel>{children}</AuthRightPanel>
    </div>
  );
}
