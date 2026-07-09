type Status = "pending" | "signed" | "expired" | "failed" | "no_request";

const config: Record<Status, { label: string; color: string }> = {
  pending: { label: "Pending", color: "var(--color-status-pending)" },
  signed: { label: "Signed", color: "var(--color-status-signed)" },
  expired: { label: "Expired", color: "var(--color-status-expired)" },
  failed: { label: "Failed", color: "var(--color-status-expired)" },
  no_request: { label: "No request", color: "var(--color-ink-muted)" },
};

export default function StatusBadge({ status }: { status: Status }) {
  const { label, color } = config[status] ?? config.no_request;

  return (
    <span
      className="text-caption rounded-[4px] px-[10px] py-[4px] inline-block"
      style={{
        color,
        backgroundColor: `color-mix(in srgb, ${color} 12%, transparent)`,
      }}
    >
      {label}
    </span>
  );
}
