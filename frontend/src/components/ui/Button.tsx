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
          "inline-flex items-center justify-center gap-2 font-semibold rounded-[var(--radius-btn)] transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed",
          {
            "gradient-btn text-white shadow-md hover:opacity-90 active:scale-[0.98]":
              variant === "primary",
            "bg-[var(--color-aria-surface-3)] text-[var(--color-aria-ink)] border border-[var(--color-aria-border-strong)] hover:border-[var(--color-aria-blue)]/40 hover:bg-[var(--color-aria-surface-2)]":
              variant === "secondary",
            "text-[var(--color-aria-muted)] hover:text-[var(--color-aria-ink)] hover:bg-[var(--color-aria-surface-3)]":
              variant === "ghost",
            "bg-red-500/10 text-[var(--color-aria-red)] border border-red-500/20 hover:bg-red-500/20":
              variant === "danger",
          },
          {
            "text-xs px-3 py-1.5": size === "sm",
            "text-sm px-4 py-2": size === "md",
            "text-sm px-5 py-2.5": size === "lg",
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
