"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "@/components/theme-provider";
import { cn } from "@/lib/utils";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      aria-label={theme === "light" ? "Ativar modo escuro" : "Ativar modo claro"}
      className={cn(
        "relative h-8 w-14 rounded-full transition-all duration-300",
        "glass neu-inset-sm",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
      )}
    >
      {/* Track interno */}
      <span
        className={cn(
          "absolute inset-0.5 rounded-full transition-all duration-300",
          theme === "dark"
            ? "bg-primary/20"
            : "bg-primary/10"
        )}
      />

      {/* Bolinha deslizante */}
      <span
        className={cn(
          "absolute top-1 h-6 w-6 rounded-full transition-all duration-300 flex items-center justify-center",
          "glass-card shadow-sm",
          theme === "light" ? "left-1" : "left-7"
        )}
      >
        {theme === "light" ? (
          <Sun className="h-3.5 w-3.5 text-accent" />
        ) : (
          <Moon className="h-3.5 w-3.5 text-primary" />
        )}
      </span>
    </button>
  );
}
