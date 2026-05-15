import { cn } from "@/lib/utils";
import { type ButtonHTMLAttributes, forwardRef } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "secondary", size = "md", children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center gap-2 rounded-[var(--radius-btn)] font-semibold transition-all duration-150 disabled:cursor-not-allowed disabled:opacity-40",
          {
            "gradient-btn text-slate-950 hover:opacity-90 active:scale-[0.98]":
              variant === "primary",
            "border border-[var(--color-aria-border-strong)] bg-white/6 text-[var(--color-aria-ink)] hover:border-[var(--color-aria-blue)]/40 hover:bg-white/8":
              variant === "secondary",
            "text-[var(--color-aria-muted)] hover:bg-white/6 hover:text-[var(--color-aria-ink)]":
              variant === "ghost",
            "bg-red-500/10 text-[var(--color-aria-red)] border border-red-500/20 hover:bg-red-500/20":
              variant === "danger",
          },
          {
            "px-3 py-2 text-xs": size === "sm",
            "px-4 py-3 text-sm": size === "md",
            "px-6 py-4 text-sm": size === "lg",
          },
          className
        )}
        {...props}
      >
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";
