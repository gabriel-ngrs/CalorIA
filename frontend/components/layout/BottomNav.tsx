"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  UtensilsCrossed,
  Droplets,
  Plus,
  MoreHorizontal,
  Scale,
  Smile,
  BarChart2,
  Bell,
  Sparkles,
  User,
  MessageCircle,
  X,
} from "lucide-react";
import { QuickMealModal } from "@/components/dashboard/QuickAddModals";

const primaryNav = [
  { href: "/dashboard",  label: "Início",     icon: LayoutDashboard },
  { href: "/refeicoes",  label: "Refeições",  icon: UtensilsCrossed },
  null, // FAB slot
  { href: "/hidratacao", label: "Hidratação", icon: Droplets },
];

const moreNav = [
  { href: "/peso",      label: "Peso",        icon: Scale },
  { href: "/humor",     label: "Humor",       icon: Smile },
  { href: "/relatorios",label: "Relatórios",  icon: BarChart2 },
  { href: "/lembretes", label: "Lembretes",   icon: Bell },
  { href: "/insights",  label: "Insights IA", icon: Sparkles },
  { href: "/perfil",    label: "Perfil",      icon: User },
  { href: "/conectar",  label: "Conectar Bot",icon: MessageCircle },
];

export function BottomNav() {
  const pathname = usePathname();
  const [fabOpen, setFabOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);

  const isMoreActive = moreNav.some((item) => pathname === item.href);

  return (
    <>
      <QuickMealModal open={fabOpen} onOpenChange={setFabOpen} />

      {/* Backdrop do drawer "Mais" */}
      {moreOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={() => setMoreOpen(false)}
        />
      )}

      {/* Drawer "Mais" — aparece acima da navbar */}
      <div
        className={cn(
          "fixed bottom-[60px] left-0 right-0 z-40 md:hidden glass border-t border-[var(--glass-border)] rounded-t-2xl shadow-2xl",
          "transition-transform duration-300 ease-out",
          moreOpen ? "translate-y-0" : "translate-y-full pointer-events-none"
        )}
      >
        {/* Handle visual */}
        <div className="flex justify-center pt-2 pb-1">
          <div className="h-1 w-10 rounded-full bg-muted-foreground/30" />
        </div>

        <div className="flex items-center justify-between px-4 pt-1 pb-2">
          <span className="text-sm font-semibold text-foreground">Mais opções</span>
          <button
            onClick={() => setMoreOpen(false)}
            className="p-1 rounded-full text-muted-foreground hover:text-foreground"
            aria-label="Fechar"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="grid grid-cols-4 gap-1 px-2 pb-4">
          {moreNav.map(({ href, label, icon: Icon }) => {
            const isActive = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                onClick={() => setMoreOpen(false)}
                className={cn(
                  "flex flex-col items-center gap-1.5 rounded-xl p-3 transition-colors",
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <Icon className="h-6 w-6 shrink-0" />
                <span className="text-[10px] font-medium text-center leading-tight">{label}</span>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Barra de navegação principal */}
      <nav className="fixed bottom-0 left-0 right-0 z-50 md:hidden glass border-t border-[var(--glass-border)]">
        <div className="flex items-center">
          {primaryNav.map((item, idx) => {
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

          {/* Botão "Mais" */}
          {(() => {
            const activeMaisItem = moreNav.find((item) => pathname === item.href);
            const ActiveIcon = activeMaisItem?.icon ?? MoreHorizontal;
            return (
              <button
                type="button"
                onClick={() => setMoreOpen(true)}
                className={cn(
                  "relative flex-1 flex flex-col items-center gap-0.5 py-2.5 transition-colors duration-150",
                  isMoreActive ? "text-primary" : "text-muted-foreground"
                )}
                aria-label="Mais opções"
              >
                {isMoreActive && (
                  <span className="absolute top-0 left-1/2 -translate-x-1/2 h-0.5 w-8 bg-primary rounded-b-full" />
                )}
                <ActiveIcon className="h-5 w-5 shrink-0" />
                <span className="text-[10px] font-medium whitespace-nowrap leading-tight">
                  {activeMaisItem?.label ?? "Mais"}
                </span>
              </button>
            );
          })()}
        </div>
      </nav>
    </>
  );
}
