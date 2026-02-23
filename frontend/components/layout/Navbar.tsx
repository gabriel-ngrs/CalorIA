"use client";

import { signOut, useSession } from "next-auth/react";
import { Button } from "@/components/ui/button";
import { LogOut, User } from "lucide-react";

export function Navbar() {
  const { data: session } = useSession();

  return (
    <header className="sticky top-0 z-40 border-b bg-background/80 backdrop-blur">
      <div className="flex h-14 items-center justify-between px-4 md:px-6">
        <span className="font-semibold text-sm md:hidden">CalorIA</span>
        <div className="ml-auto flex items-center gap-3">
          <span className="hidden text-sm text-muted-foreground md:block">
            <User className="inline h-3.5 w-3.5 mr-1" />
            {session?.user?.name ?? session?.user?.email}
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => signOut({ callbackUrl: "/login" })}
            className="gap-1.5 text-muted-foreground"
          >
            <LogOut className="h-4 w-4" />
            <span className="hidden md:inline">Sair</span>
          </Button>
        </div>
      </div>
    </header>
  );
}
