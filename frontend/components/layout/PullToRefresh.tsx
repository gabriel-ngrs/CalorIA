"use client";

import { useEffect, useRef, useState } from "react";
import { RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  onRefresh: () => Promise<void> | void;
  children: React.ReactNode;
  className?: string;
}

const THRESHOLD = 72; // pixels to pull before triggering

export function PullToRefresh({ onRefresh, children, className }: Props) {
  const [pullY, setPullY] = useState(0);
  const [refreshing, setRefreshing] = useState(false);
  const startY = useRef<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    function onTouchStart(e: TouchEvent) {
      // Only trigger when scrolled to top
      if (window.scrollY > 0) return;
      startY.current = e.touches[0].clientY;
    }

    function onTouchMove(e: TouchEvent) {
      if (startY.current === null || refreshing) return;
      const dy = e.touches[0].clientY - startY.current;
      if (dy > 0) {
        e.preventDefault();
        setPullY(Math.min(dy * 0.45, THRESHOLD + 20));
      }
    }

    async function onTouchEnd() {
      if (pullY >= THRESHOLD && !refreshing) {
        setRefreshing(true);
        try {
          await onRefresh();
        } finally {
          setRefreshing(false);
        }
      }
      startY.current = null;
      setPullY(0);
    }

    el.addEventListener("touchstart", onTouchStart, { passive: true });
    el.addEventListener("touchmove", onTouchMove, { passive: false });
    el.addEventListener("touchend", onTouchEnd);

    return () => {
      el.removeEventListener("touchstart", onTouchStart);
      el.removeEventListener("touchmove", onTouchMove);
      el.removeEventListener("touchend", onTouchEnd);
    };
  }, [pullY, refreshing, onRefresh]);

  const progress = Math.min(pullY / THRESHOLD, 1);
  const triggered = pullY >= THRESHOLD;

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      {/* Pull indicator */}
      <div
        className="absolute top-0 left-0 right-0 flex justify-center overflow-hidden pointer-events-none z-10"
        style={{ height: Math.max(pullY, refreshing ? 48 : 0), transition: pullY === 0 ? "height 0.3s ease" : "none" }}
      >
        <div
          className={cn(
            "flex items-center justify-center w-9 h-9 rounded-full mt-2 transition-colors",
            triggered || refreshing ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
          )}
          style={{ opacity: Math.max(progress, refreshing ? 1 : 0) }}
        >
          <RefreshCw
            className={cn("h-4 w-4", refreshing && "animate-spin")}
            style={{ transform: `rotate(${progress * 180}deg)`, transition: refreshing ? "none" : "transform 0.1s linear" }}
          />
        </div>
      </div>

      {/* Content */}
      <div style={{ transform: `translateY(${pullY > 0 || refreshing ? Math.max(pullY, refreshing ? 48 : 0) : 0}px)`, transition: pullY === 0 ? "transform 0.3s ease" : "none" }}>
        {children}
      </div>
    </div>
  );
}
