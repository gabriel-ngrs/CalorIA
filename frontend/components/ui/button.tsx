import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-xl text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50 active:scale-[0.97]",
  {
    variants: {
      variant: {
        /* Primário: gradiente verde esmeralda com glow */
        default:
          "bg-gradient-to-br from-primary to-[hsl(142_75%_42%)] text-primary-foreground " +
          "shadow-glow-sm hover:shadow-glow-primary hover:brightness-110",

        /* Destructivo */
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90 " +
          "shadow-[0_2px_10px_hsl(var(--destructive)/0.3)]",

        /* Contorno glass */
        outline:
          "glass text-foreground border border-[var(--glass-border)] " +
          "hover:bg-primary/10 hover:border-primary/40 hover:text-primary",

        /* Secundário neumórfico */
        secondary:
          "bg-secondary text-secondary-foreground neu-raised-sm " +
          "hover:neu-raised hover:bg-secondary/80",

        /* Ghost */
        ghost:
          "text-muted-foreground hover:glass hover:text-foreground rounded-xl",

        /* Link */
        link: "text-primary underline-offset-4 hover:underline",

        /* Glass + glow (acento) */
        glass:
          "glass text-foreground glass-hover " +
          "hover:border-primary/30 hover:text-primary",
      },
      size: {
        default: "h-10 px-5 py-2",
        sm: "h-9 rounded-lg px-3 text-xs",
        lg: "h-11 rounded-xl px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
