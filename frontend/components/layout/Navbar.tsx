"use client";

import { signOut, useSession } from "next-auth/react";
import { Button } from "@/components/ui/button";
import { LogOut, User } from "lucide-react";

export function Navbar() {
  const { data: session } = useSession();

  return (
    <header className="sticky top-0 z-40 glass border-b border-[var(--glass-border)]">
      <div className="flex h-14 items-center justify-between px-4 md:px-6">
        <span className="font-bold text-lg gradient-text md:hidden">CalorIA</span>

        <div className="ml-auto flex items-center gap-3">
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-xl glass neu-inset-sm">
            <User className="h-3.5 w-3.5 text-primary" />
            <span className="text-sm text-foreground/80">
              {session?.user?.name ?? session?.user?.email}
            </span>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => signOut({ callbackUrl: "/login" })}
            className="gap-1.5 text-muted-foreground hover:text-destructive"
          >
            <LogOut className="h-4 w-4" />
            <span className="hidden md:inline">Sair</span>
          </Button>
        </div>
      </div>
    </header>
  );
}
