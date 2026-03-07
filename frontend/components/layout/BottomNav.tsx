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
  { href: "/dashboard",  label: "Dashboard",  icon: LayoutDashboard },
  { href: "/refeicoes",  label: "Refeições",   icon: UtensilsCrossed },
  { href: "/peso",       label: "Peso",        icon: Scale },
  { href: "/hidratacao", label: "Hidratação",  icon: Droplets },
  { href: "/humor",      label: "Humor",       icon: Smile },
  { href: "/lembretes",  label: "Lembretes",   icon: Bell },
  { href: "/insights",   label: "Insights",    icon: Sparkles },
  { href: "/perfil",     label: "Perfil",      icon: User },
  { href: "/conectar",   label: "Conectar",    icon: MessageCircle },
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 md:hidden glass border-t border-[var(--glass-border)]">
      <div className="flex overflow-x-auto [&::-webkit-scrollbar]:hidden [scrollbar-width:none]">
        {nav.map(({ href, label, icon: Icon }) => {
          const isActive =
            pathname === href || (href === "/dashboard" && pathname === "/");

          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "relative flex flex-col items-center gap-0.5 px-3 py-2.5 min-w-[64px] shrink-0 transition-colors duration-150",
                isActive ? "text-primary" : "text-muted-foreground"
              )}
            >
              {isActive && (
                <span className="absolute top-0 left-1/2 -translate-x-1/2 h-0.5 w-8 bg-primary rounded-b-full" />
              )}
              <Icon className="h-5 w-5 shrink-0" />
              <span className="text-[10px] font-medium whitespace-nowrap leading-tight">
                {label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
