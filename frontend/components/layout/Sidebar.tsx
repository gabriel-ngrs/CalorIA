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
    <aside className="hidden md:flex flex-col w-60 border-r bg-card min-h-screen py-6 px-3">
      <div className="mb-8 px-3">
        <h1 className="text-xl font-bold text-primary">CalorIA</h1>
        <p className="text-xs text-muted-foreground">Diário alimentar inteligente</p>
      </div>

      <nav className="flex-1 space-y-1">
        {nav.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
              pathname === href || (href === "/dashboard" && pathname === "/")
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            )}
          >
            <Icon className="h-4 w-4 shrink-0" />
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
