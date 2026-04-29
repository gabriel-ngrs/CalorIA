"use client";

import { useTheme } from "@/components/theme-provider";
import { Sun, Moon } from "lucide-react";

export function AuthRightPanel({ children }: { children: React.ReactNode }) {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="flex-1 relative flex flex-col items-center justify-center min-h-screen bg-background px-6 py-12 overflow-hidden">

      {/* Dot grid decorativo */}
      <div
        className="absolute inset-0 pointer-events-none opacity-100"
        style={{
          backgroundImage: "radial-gradient(circle, rgba(100,116,139,0.22) 1px, transparent 1px)",
          backgroundSize: "28px 28px",
        }}
      />

      {/* Glow verde sutil no centro */}
      <div
        className="absolute pointer-events-none"
        style={{
          top: "30%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          width: "500px",
          height: "400px",
          background: "radial-gradient(ellipse, rgba(52,211,153,0.06) 0%, transparent 70%)",
          filter: "blur(30px)",
        }}
      />

      {/* Botão de tema — canto superior direito */}
      <button
        onClick={toggleTheme}
        aria-label="Alternar tema"
        className="absolute top-5 right-5 z-20 flex items-center gap-2 rounded-xl border border-border bg-card px-3.5 py-2 text-sm font-medium text-muted-foreground shadow-sm transition-all hover:text-foreground hover:border-primary/40 hover:shadow-md"
      >
        {theme === "dark" ? (
          <>
            <Sun size={15} />
            <span className="hidden sm:inline">Claro</span>
          </>
        ) : (
          <>
            <Moon size={15} />
            <span className="hidden sm:inline">Escuro</span>
          </>
        )}
      </button>

      {/* Conteúdo (form) */}
      <div className="relative z-10 w-full flex flex-col items-center">
        {children}
      </div>
    </div>
  );
}
