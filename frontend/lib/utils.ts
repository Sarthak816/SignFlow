/**
 * Shared utility functions.
 */

/**
 * Returns a human-readable relative time string, e.g. "3 minutes".
 * Used for the "last updated X ago" timestamp on document cards.
 */
export function formatDistanceToNow(isoString: string): string {
  try {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSec = Math.floor(diffMs / 1000);

    if (diffSec < 60) return `${diffSec} second${diffSec !== 1 ? "s" : ""}`;
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin} minute${diffMin !== 1 ? "s" : ""}`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr} hour${diffHr !== 1 ? "s" : ""}`;
    const diffDay = Math.floor(diffHr / 24);
    return `${diffDay} day${diffDay !== 1 ? "s" : ""}`;
  } catch {
    return "unknown time";
  }
}

/**
 * Trigger a file download in the browser from a Blob.
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
