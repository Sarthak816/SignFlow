"use client";

import { useRef, useState, DragEvent, ChangeEvent } from "react";

interface UploadDropzoneProps {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
  error?: string;
}

export default function UploadDropzone({ onFileSelected, disabled, error }: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  function handleDragOver(e: DragEvent) {
    e.preventDefault();
    if (!disabled) setIsDragging(true);
  }

  function handleDragLeave() {
    setIsDragging(false);
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault();
    setIsDragging(false);
    if (disabled) return;
    const file = e.dataTransfer.files[0];
    if (file) onFileSelected(file);
  }

  function handleChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) onFileSelected(file);
  }

  return (
    <div
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-label="Upload PDF — drag and drop or click to browse"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => !disabled && inputRef.current?.click()}
      onKeyDown={(e) => e.key === "Enter" && !disabled && inputRef.current?.click()}
      className={[
        "rounded-[6px] p-[40px] text-center cursor-pointer transition-all duration-150",
        "border",
        isDragging
          ? "border-[var(--color-signature)] border-solid bg-[color-mix(in_srgb,var(--color-signature)_4%,transparent)]"
          : error
          ? "border-[var(--color-status-expired)] border-dashed"
          : "border-[var(--color-line)] border-dashed",
        disabled ? "opacity-40 cursor-not-allowed" : "hover:border-[var(--color-signature)]",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-signature)] focus-visible:ring-offset-2",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,application/pdf"
        className="hidden"
        onChange={handleChange}
        disabled={disabled}
        aria-hidden="true"
      />
      <p className="text-body text-[var(--color-ink)] mb-[4px]">
        Drag a PDF here, or click to browse
      </p>
      <p className="text-body-sm text-[var(--color-ink-muted)]">PDF only, up to 10MB</p>
      {error && (
        <p className="text-body-sm text-[var(--color-status-expired)] mt-[8px]">{error}</p>
      )}
    </div>
  );
}
