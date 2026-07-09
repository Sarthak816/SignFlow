"use client";

import { InputHTMLAttributes, forwardRef } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, className = "", id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, "-");

    return (
      <div className="flex flex-col gap-[6px]">
        {label && (
          <label
            htmlFor={inputId}
            className="text-body-sm text-[var(--color-ink-muted)]"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={[
            "bg-[var(--color-paper)] rounded-[6px] px-[12px] py-[10px]",
            "text-body text-[var(--color-ink)]",
            "border transition-colors duration-150",
            error
              ? "border-[var(--color-status-expired)] focus:border-[var(--color-status-expired)]"
              : "border-[var(--color-line)] focus:border-[var(--color-signature)]",
            "outline-none focus:ring-2 focus:ring-[var(--color-signature)]/20 focus:ring-offset-0",
            "placeholder:text-[var(--color-ink-muted)]",
            "disabled:opacity-40 disabled:cursor-not-allowed",
            className,
          ]
            .filter(Boolean)
            .join(" ")}
          {...props}
        />
        {error && (
          <p className="text-body-sm text-[var(--color-status-expired)]">{error}</p>
        )}
        {hint && !error && (
          <p className="text-body-sm text-[var(--color-ink-muted)]">{hint}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
export default Input;
