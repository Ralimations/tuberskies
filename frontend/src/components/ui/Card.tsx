import { cn } from "@/lib/utils";
import { type HTMLAttributes, forwardRef } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  glow?: "blue" | "purple" | "none";
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, glow = "none", children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] transition-all duration-200",
          glow === "blue" && "glow-blue border-[var(--color-aria-blue)]/20",
          glow === "purple" && "glow-purple border-[var(--color-aria-purple)]/20",
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);
Card.displayName = "Card";

export function CardHeader({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("px-6 py-4 border-b border-[var(--color-aria-border)]", className)} {...props}>
      {children}
    </div>
  );
}

export function CardContent({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("px-6 py-4", className)} {...props}>
      {children}
    </div>
  );
}
