"use client";

import { useEffect, useRef, useState } from "react";
import { RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  onRefresh: () => Promise<void> | void;
  children: React.ReactNode;
  className?: string;
}

const THRESHOLD = 72;

export function PullToRefresh({ onRefresh, children, className }: Props) {
  const [pullY, setPullY] = useState(0);
  const [refreshing, setRefreshing] = useState(false);

  // Use refs for values accessed inside event handlers to avoid stale closures
  // and to prevent the effect from re-running on every state change
  const startY = useRef<number | null>(null);
  const pullYRef = useRef(0);
  const refreshingRef = useRef(false);
  const onRefreshRef = useRef(onRefresh);
  const containerRef = useRef<HTMLDivElement>(null);

  // Keep onRefreshRef current without triggering effect re-registration
  useEffect(() => {
    onRefreshRef.current = onRefresh;
  }, [onRefresh]);

  // Event listeners registered once — reads state via refs, not closure captures
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    function onTouchStart(e: TouchEvent) {
      if (window.scrollY > 0) return;
      startY.current = e.touches[0].clientY;
    }

    function onTouchMove(e: TouchEvent) {
      if (startY.current === null || refreshingRef.current) return;
      const dy = e.touches[0].clientY - startY.current;
      if (dy > 0) {
        e.preventDefault();
        const clamped = Math.min(dy * 0.45, THRESHOLD + 20);
        pullYRef.current = clamped;
        setPullY(clamped);
      }
    }

    async function onTouchEnd() {
      if (pullYRef.current >= THRESHOLD && !refreshingRef.current) {
        refreshingRef.current = true;
        setRefreshing(true);
        setPullY(0);
        pullYRef.current = 0;
        try {
          await onRefreshRef.current();
        } finally {
          refreshingRef.current = false;
          setRefreshing(false);
        }
      } else {
        startY.current = null;
        pullYRef.current = 0;
        setPullY(0);
      }
    }

    el.addEventListener("touchstart", onTouchStart, { passive: true });
    el.addEventListener("touchmove", onTouchMove, { passive: false });
    el.addEventListener("touchend", onTouchEnd);

    return () => {
      el.removeEventListener("touchstart", onTouchStart);
      el.removeEventListener("touchmove", onTouchMove);
      el.removeEventListener("touchend", onTouchEnd);
    };
  }, []); // empty deps — handlers use refs, registered once on mount

  const progress = Math.min(pullY / THRESHOLD, 1);
  const triggered = pullY >= THRESHOLD;

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      {/* Pull indicator */}
      <div
        className="absolute top-0 left-0 right-0 flex justify-center overflow-hidden pointer-events-none z-10"
        style={{
          height: Math.max(pullY, refreshing ? 48 : 0),
          transition: pullY === 0 ? "height 0.3s ease" : "none",
        }}
      >
        <div
          className={cn(
            "flex items-center justify-center w-9 h-9 rounded-full mt-2 transition-colors",
            triggered || refreshing
              ? "bg-primary text-primary-foreground"
              : "bg-muted text-muted-foreground"
          )}
          style={{ opacity: Math.max(progress, refreshing ? 1 : 0) }}
        >
          <RefreshCw
            className={cn("h-4 w-4", refreshing && "animate-spin")}
            style={{
              transform: `rotate(${progress * 180}deg)`,
              transition: refreshing ? "none" : "transform 0.1s linear",
            }}
          />
        </div>
      </div>

      {/* Content */}
      <div
        style={{
          transform: `translateY(${pullY > 0 || refreshing ? Math.max(pullY, refreshing ? 48 : 0) : 0}px)`,
          transition: pullY === 0 ? "transform 0.3s ease" : "none",
        }}
      >
        {children}
      </div>
    </div>
  );
}
