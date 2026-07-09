"use client";

import { motion } from "motion/react";
import { ButtonHTMLAttributes, forwardRef } from "react";

type Variant = "primary" | "secondary" | "destructive";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  loading?: boolean;
}

const base =
  "inline-flex items-center justify-center rounded-[6px] px-[18px] py-[10px] text-[14px] font-semibold font-[family-name:var(--font-body)] transition-colors duration-150 disabled:opacity-40 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-signature)] focus-visible:ring-offset-2";

const variants: Record<Variant, string> = {
  primary:
    "bg-[var(--color-signature)] text-white hover:bg-[var(--color-signature-hover)] hover:shadow-[0_1px_2px_rgba(0,0,0,0.06)]",
  secondary:
    "bg-[var(--color-paper)] text-[var(--color-ink)] border border-[var(--color-line)] hover:bg-[var(--color-line)]",
  destructive:
    "bg-[var(--color-paper)] text-[var(--color-status-expired)] border border-[var(--color-status-expired)] hover:bg-[var(--color-status-expired)] hover:text-white",
};

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", loading = false, children, className = "", disabled, ...props }, ref) => {
    return (
      <motion.button
        ref={ref}
        whileTap={{ scale: 0.98 }}
        className={`${base} ${variants[variant]} ${className}`}
        disabled={disabled || loading}
        onClick={props.onClick}
        type={props.type}
        form={props.form}
        aria-label={props["aria-label"]}
      >
        {loading ? (
          <span className="flex items-center gap-2">
            <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
            {children}
          </span>
        ) : (
          children
        )}
      </motion.button>
    );
  }
);

Button.displayName = "Button";
export default Button;
