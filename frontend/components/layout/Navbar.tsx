"use client";

import { signOut, useSession } from "next-auth/react";
import { Button } from "@/components/ui/button";
import { NotificationBell } from "@/components/layout/NotificationBell";
import { LogOut } from "lucide-react";
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
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-sm border-b border-gray-100">
      <div className="flex h-14 items-center justify-between px-4 md:px-6">
        {/* Logo visível apenas no mobile */}
        <span className="font-bold text-lg gradient-text md:hidden">CalorIA</span>

        <div className="ml-auto flex items-center gap-2">
          {/* Usuário */}
          {session?.user && (
            <div className="hidden md:flex items-center gap-2 px-2.5 py-1 rounded-lg text-muted-foreground text-sm">
              <span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary/15 text-primary font-semibold text-xs shrink-0 uppercase">
                {(session.user.name ?? session.user.email ?? "?")[0]}
              </span>
              <span className="max-w-[120px] truncate">
                {session.user.name ?? session.user.email}
              </span>
            </div>
          )}

          {/* Notificações */}
          <NotificationBell />

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
