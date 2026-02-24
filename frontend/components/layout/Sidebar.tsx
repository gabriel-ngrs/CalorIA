"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  UtensilsCrossed,
  Scale,
  Droplets,
  Smile,
  Bell,
  User,
  MessageCircle,
  Sparkles,
} from "lucide-react";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/refeicoes", label: "Refeições", icon: UtensilsCrossed },
  { href: "/peso", label: "Peso", icon: Scale },
  { href: "/hidratacao", label: "Hidratação", icon: Droplets },
  { href: "/humor", label: "Humor", icon: Smile },
  { href: "/lembretes", label: "Lembretes", icon: Bell },
  { href: "/insights", label: "Insights IA", icon: Sparkles },
  { href: "/perfil", label: "Perfil", icon: User },
  { href: "/conectar", label: "Conectar Bot", icon: MessageCircle },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        "hidden md:flex flex-col w-60 min-h-screen py-6 px-3",
        "glass border-r border-[var(--glass-border)]",
        "sticky top-0 h-screen"
      )}
    >
      {/* Logo */}
      <div className="mb-8 px-3">
        <h1 className="text-2xl font-bold gradient-text tracking-tight">CalorIA</h1>
        <p className="text-xs text-muted-foreground mt-0.5">Diário alimentar inteligente</p>
      </div>

      {/* Divisor decorativo */}
      <div
        className="mx-3 mb-4 h-px rounded-full"
        style={{
          background:
            "linear-gradient(90deg, transparent, hsl(var(--primary) / 0.4), transparent)",
        }}
      />

      <nav className="flex-1 space-y-0.5">
        {nav.map(({ href, label, icon: Icon }) => {
          const isActive =
            pathname === href || (href === "/dashboard" && pathname === "/");

          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium",
                "transition-all duration-200",
                isActive
                  ? [
                      "glass-card text-primary",
                      "border border-primary/25",
                      "shadow-[0_0_12px_hsl(var(--primary)/0.15)]",
                    ]
                  : [
                      "text-muted-foreground",
                      "hover:glass hover:text-foreground",
                      "hover:border hover:border-[var(--glass-border)]",
                    ]
              )}
            >
              <Icon
                className={cn(
                  "h-4 w-4 shrink-0 transition-colors",
                  isActive ? "text-primary" : "text-muted-foreground"
                )}
              />
              {label}
              {isActive && (
                <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary glow-primary-sm" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Rodapé da sidebar */}
      <div
        className="mx-3 mt-4 mb-2 h-px rounded-full"
        style={{
          background:
            "linear-gradient(90deg, transparent, hsl(var(--primary) / 0.4), transparent)",
        }}
      />
      <p className="px-3 text-[10px] text-muted-foreground/50 text-center">
        v0.1 · Powered by Gemini
      </p>
    </aside>
  );
}
