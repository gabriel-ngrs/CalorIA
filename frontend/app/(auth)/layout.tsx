import { AuthBackground } from "@/components/auth/AuthBackground";
import { AuthBrand } from "@/components/auth/AuthBrand";
import { Plasma } from "@/components/auth/Plasma";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative min-h-screen overflow-hidden bg-[#eef4f0]">
      <Plasma speed={0.35} scale={1.1} opacity={0.6} />
      <AuthBackground />

      {/* Conteúdo: centralizado, safe area no mobile */}
      <div className="relative z-10 min-h-screen flex flex-col items-center justify-center px-4 py-12 sm:py-8">
        <AuthBrand />
        {children}
      </div>
    </div>
  );
}
