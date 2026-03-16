"use client";

import { signOut, useSession } from "next-auth/react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { NotificationBell } from "@/components/layout/NotificationBell";
import { LogOut, User } from "lucide-react";
import api from "@/lib/api";

async function handleLogout(refreshToken?: string) {
  if (refreshToken) {
    try {
      await api.post("/api/v1/auth/logout", { refresh_token: refreshToken });
    } catch {
      // Ignora erro — invalida sessão local de qualquer forma
    }
  }
  await signOut({ callbackUrl: "/login" });
}

export function Navbar() {
  const { data: session } = useSession();

  return (
    <header className="sticky top-0 z-40 glass border-b border-[var(--glass-border)]">
      <div className="flex h-14 items-center justify-between px-4 md:px-6">
        {/* Logo visível apenas no mobile */}
        <span className="font-bold text-lg gradient-text md:hidden">CalorIA</span>

        <div className="ml-auto flex items-center gap-2">
          {/* Usuário */}
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-muted-foreground text-sm">
            <User className="h-3.5 w-3.5" />
            <span>{session?.user?.name ?? session?.user?.email}</span>
          </div>

          {/* Notificações */}
          <NotificationBell />

          {/* Toggle de tema */}
          <ThemeToggle />

          {/* Sair */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleLogout(session?.refreshToken)}
            className="gap-1.5 text-muted-foreground hover:text-destructive"
          >
            <LogOut className="h-4 w-4" />
            <span className="hidden md:inline text-sm">Sair</span>
          </Button>
        </div>
      </div>
    </header>
  );
}
