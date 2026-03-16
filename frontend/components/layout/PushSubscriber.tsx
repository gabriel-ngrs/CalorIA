"use client";

import { useEffect, useRef, useState } from "react";
import { Bell, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { usePushNotifications } from "@/lib/hooks/usePushNotifications";

/**
 * PushSubscriber — mounts silently in the dashboard layout.
 *
 * Behaviour:
 * - If push is not supported, does nothing.
 * - If Notification.permission === 'granted' and not yet subscribed, auto-subscribes silently.
 * - If Notification.permission === 'default', shows a subtle dismissible banner once per session.
 * - If Notification.permission === 'denied', does nothing.
 */
export function PushSubscriber() {
  const { isSupported, isSubscribed, permission, subscribeToPush } =
    usePushNotifications();
  const [showBanner, setShowBanner] = useState(false);
  const attemptedRef = useRef(false);

  useEffect(() => {
    if (!isSupported || attemptedRef.current) return;

    if (permission === "granted" && !isSubscribed) {
      // Silent auto-subscribe
      attemptedRef.current = true;
      subscribeToPush().catch(() => {
        // Silently ignore — push is optional
      });
    } else if (permission === "default" && !isSubscribed) {
      // Show subtle banner
      setShowBanner(true);
    }
  }, [isSupported, permission, isSubscribed, subscribeToPush]);

  if (!showBanner) return null;

  return (
    <div className="fixed bottom-[72px] md:bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-80 z-50 animate-fade-in">
      <div className="glass border border-primary/20 rounded-xl p-3 shadow-2xl flex items-start gap-3">
        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 shrink-0">
          <Bell className="h-4 w-4 text-primary" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-foreground leading-tight">
            Ativar notificações
          </p>
          <p className="text-xs text-muted-foreground mt-0.5 leading-snug">
            Receba lembretes e resumos diários mesmo com o app fechado.
          </p>
          <div className="flex gap-2 mt-2.5">
            <Button
              size="sm"
              className="h-7 text-xs px-3"
              onClick={async () => {
                setShowBanner(false);
                attemptedRef.current = true;
                await subscribeToPush();
              }}
            >
              Ativar
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 text-xs px-2 text-muted-foreground"
              onClick={() => setShowBanner(false)}
            >
              Agora não
            </Button>
          </div>
        </div>
        <button
          type="button"
          onClick={() => setShowBanner(false)}
          className="text-muted-foreground hover:text-foreground transition-colors shrink-0 mt-0.5"
          aria-label="Fechar"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
