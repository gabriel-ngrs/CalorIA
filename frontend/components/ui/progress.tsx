"use client";

import * as React from "react";
import * as ProgressPrimitive from "@radix-ui/react-progress";
import { cn } from "@/lib/utils";

interface ProgressProps extends React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root> {
  indicatorColor?: string;
}

const Progress = React.forwardRef<
  React.ElementRef<typeof ProgressPrimitive.Root>,
  ProgressProps
>(({ className, value, indicatorColor, ...props }, ref) => {
  const isGradient = indicatorColor?.startsWith("linear-gradient") || indicatorColor?.startsWith("radial-gradient");
  const indicatorStyle = indicatorColor
    ? {
        transform: `translateX(-${100 - (value || 0)}%)`,
        background: indicatorColor,
        boxShadow: isGradient ? "0 0 8px rgba(59,130,246,0.45)" : `0 0 8px ${indicatorColor}66`,
      }
    : {
        transform: `translateX(-${100 - (value || 0)}%)`,
        background: "hsl(var(--primary))",
      };

  return (
    <ProgressPrimitive.Root
      ref={ref}
      className={cn(
        "relative h-2.5 w-full overflow-hidden rounded-full",
        "bg-muted",
        className
      )}
      {...props}
    >
      <ProgressPrimitive.Indicator
        className="h-full w-full flex-1 transition-all duration-500 ease-out rounded-full"
        style={indicatorStyle}
      />
    </ProgressPrimitive.Root>
  );
});
Progress.displayName = ProgressPrimitive.Root.displayName;

export { Progress };
