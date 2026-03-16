"use client";

import { useState } from "react";
import {
  Bell,
  BellOff,
  CheckCheck,
  Droplets,
  BarChart2,
  CalendarCheck,
  Info,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  useNotifications,
  useMarkNotificationRead,
  useMarkAllRead,
} from "@/lib/hooks/useNotifications";
import type { AppNotification, NotificationType } from "@/types";
import { cn } from "@/lib/utils";

function formatRelativeTime(isoString: string): string {
  const now = Date.now();
  const then = new Date(isoString).getTime();
  const diff = Math.floor((now - then) / 1000); // seconds

  if (diff < 60) return "agora";
  if (diff < 3600) return `há ${Math.floor(diff / 60)} min`;
  if (diff < 86400) return `há ${Math.floor(diff / 3600)}h`;
  if (diff < 604800) return `há ${Math.floor(diff / 86400)}d`;
  return new Date(isoString).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
  });
}

function NotificationIcon({ type }: { type: NotificationType }) {
  const cls = "h-4 w-4 shrink-0";
  switch (type) {
    case "hydration":
      return <Droplets className={cn(cls, "text-blue-400")} />;
    case "daily_summary":
      return <CalendarCheck className={cn(cls, "text-purple-400")} />;
    case "weekly_report":
      return <BarChart2 className={cn(cls, "text-green-400")} />;
    case "system":
      return <Info className={cn(cls, "text-yellow-400")} />;
    case "reminder":
    default:
      return <Bell className={cn(cls, "text-primary")} />;
  }
}

function NotificationItem({
  notification,
  onRead,
}: {
  notification: AppNotification;
  onRead: (id: number) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => !notification.read && onRead(notification.id)}
      className={cn(
        "w-full text-left flex items-start gap-3 px-3 py-2.5 rounded-lg transition-colors duration-150",
        notification.read
          ? "opacity-50 cursor-default"
          : "hover:bg-muted/60 cursor-pointer"
      )}
    >
      <div className="mt-0.5 flex-shrink-0">
        <NotificationIcon type={notification.type} />
      </div>
      <div className="flex-1 min-w-0">
        <p
          className={cn(
            "text-sm leading-tight truncate",
            notification.read ? "font-normal text-muted-foreground" : "font-semibold text-foreground"
          )}
        >
          {notification.title}
        </p>
        <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2 leading-snug">
          {notification.body}
        </p>
        <p className="text-[10px] text-muted-foreground/60 mt-1">
          {formatRelativeTime(notification.created_at)}
        </p>
      </div>
      {!notification.read && (
        <span className="mt-1.5 h-2 w-2 rounded-full bg-primary shrink-0" />
      )}
    </button>
  );
}

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const { data: notifications } = useNotifications(10);
  const markRead = useMarkNotificationRead();
  const markAll = useMarkAllRead();

  const unreadCount = (notifications ?? []).filter((n) => !n.read).length;
  const hasUnread = unreadCount > 0;
  const badgeLabel = unreadCount > 9 ? "9+" : String(unreadCount);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative h-9 w-9 text-muted-foreground hover:text-foreground"
          aria-label={`Notificações${hasUnread ? ` (${badgeLabel} não lidas)` : ""}`}
        >
          {hasUnread ? (
            <Bell className="h-4 w-4 fill-primary text-primary" />
          ) : (
            <Bell className="h-4 w-4" />
          )}
          {hasUnread && (
            <span className="absolute -top-0.5 -right-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[9px] font-bold text-white leading-none shadow-sm">
              {badgeLabel}
            </span>
          )}
        </Button>
      </PopoverTrigger>

      <PopoverContent
        align="end"
        sideOffset={8}
        className="w-80 p-0 glass border border-[var(--glass-border)] shadow-2xl"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-3 py-2.5 border-b border-[var(--glass-border)]">
          <span className="text-sm font-semibold text-foreground">
            Notificações
          </span>
          {hasUnread && (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 gap-1.5 text-xs text-muted-foreground hover:text-foreground px-2"
              onClick={() => markAll.mutate()}
              disabled={markAll.isPending}
            >
              <CheckCheck className="h-3.5 w-3.5" />
              Marcar todas como lidas
            </Button>
          )}
        </div>

        {/* List */}
        <div className="max-h-[360px] overflow-y-auto py-1">
          {!notifications || notifications.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-10 px-4 text-center">
              <BellOff className="h-8 w-8 text-muted-foreground/30" />
              <p className="text-sm text-muted-foreground">
                Nenhuma notificação
              </p>
            </div>
          ) : (
            notifications.map((n) => (
              <NotificationItem
                key={n.id}
                notification={n}
                onRead={(id) => markRead.mutate(id)}
              />
            ))
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}
