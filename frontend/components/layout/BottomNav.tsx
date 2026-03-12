"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  UtensilsCrossed,
  Droplets,
  Smile,
  User,
  Plus,
} from "lucide-react";
import { QuickMealModal } from "@/components/dashboard/QuickAddModals";

const nav = [
  { href: "/dashboard",  label: "Início",      icon: LayoutDashboard },
  { href: "/refeicoes",  label: "Refeições",   icon: UtensilsCrossed },
  null, // FAB slot
  { href: "/hidratacao", label: "Hidratação",  icon: Droplets },
  { href: "/perfil",     label: "Perfil",      icon: User },
];

export function BottomNav() {
  const pathname = usePathname();
  const [fabOpen, setFabOpen] = useState(false);

  return (
    <>
      <QuickMealModal open={fabOpen} onOpenChange={setFabOpen} />

      <nav className="fixed bottom-0 left-0 right-0 z-50 md:hidden glass border-t border-[var(--glass-border)]">
        <div className="flex items-center">
          {nav.map((item, i) => {
            // FAB slot — botão de ação primária
            if (item === null) {
              return (
                <div key="fab" className="flex-1 flex justify-center -mt-5">
                  <button
                    type="button"
                    onClick={() => setFabOpen(true)}
                    className="w-14 h-14 rounded-full bg-primary text-primary-foreground shadow-lg shadow-primary/30 flex items-center justify-center transition-transform active:scale-95 hover:bg-primary/90 cursor-pointer"
                    aria-label="Adicionar refeição"
                  >
                    <Plus className="h-6 w-6" />
                  </button>
                </div>
              );
            }

            const { href, label, icon: Icon } = item;
            const isActive = pathname === href || (href === "/dashboard" && pathname === "/");

            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "relative flex-1 flex flex-col items-center gap-0.5 py-2.5 transition-colors duration-150",
                  isActive ? "text-primary" : "text-muted-foreground"
                )}
              >
                {isActive && (
                  <span className="absolute top-0 left-1/2 -translate-x-1/2 h-0.5 w-8 bg-primary rounded-b-full" />
                )}
                <Icon className="h-5 w-5 shrink-0" />
                <span className="text-[10px] font-medium whitespace-nowrap leading-tight">{label}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </>
  );
}
