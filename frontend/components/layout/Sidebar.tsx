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
    <aside className="hidden md:flex flex-col w-56 min-h-screen sticky top-0 h-screen glass border-r border-[var(--glass-border)] py-5 px-3">
      {/* Logo */}
      <div className="px-2 mb-6">
        <h1 className="text-xl font-bold gradient-text tracking-tight">CalorIA</h1>
        <p className="text-[11px] text-muted-foreground mt-0.5">Diário alimentar inteligente</p>
      </div>

      <div className="divider-gradient mx-2 mb-4" />

      {/* Nav */}
      <nav className="flex-1 space-y-0.5">
        {nav.map(({ href, label, icon: Icon }) => {
          const isActive =
            pathname === href || (href === "/dashboard" && pathname === "/");

          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm font-medium",
                "transition-all duration-150",
                isActive
                  ? "bg-primary/10 text-primary border border-primary/20"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <Icon className={cn("h-4 w-4 shrink-0", isActive && "text-primary")} />
              {label}
              {isActive && (
                <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Rodapé */}
      <div className="divider-gradient mx-2 mt-4 mb-3" />
      <p className="px-2 text-[10px] text-muted-foreground/50 text-center">
        V0.1 Powered by Gabriel Negreiros
      </p>
    </aside>
  );
}
