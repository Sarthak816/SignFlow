"use client";

import { motion } from "motion/react";
import StatusBadge from "@/components/StatusBadge";
import Button from "@/components/ui/Button";
import { formatDistanceToNow } from "@/lib/utils";

type Status = "pending" | "signed" | "expired" | "failed" | "no_request";

interface Signer {
  identifier: string;
  display_name?: string | null;
  status: string;
  signer_url: string;
  signed_at?: string | null;
}

interface DocumentCardProps {
  signatureRequestId: string;
  originalFilename: string;
  status: Status;
  signers: Signer[];
  updatedAt: string;
  refreshFailed?: boolean;
  onRefresh: () => void;
  onDownload: () => void;
  refreshing?: boolean;
  downloading?: boolean;
}

const borderColor: Record<Status, string> = {
  pending: "var(--color-status-pending)",
  signed: "var(--color-status-signed)",
  expired: "var(--color-status-expired)",
  failed: "var(--color-status-expired)",
  no_request: "var(--color-line)",
};

export default function DocumentCard({
  signatureRequestId,
  originalFilename,
  status,
  signers,
  updatedAt,
  refreshFailed,
  onRefresh,
  onDownload,
  refreshing,
  downloading,
}: DocumentCardProps) {
  const signer = signers[0];

  return (
    <motion.div
      whileHover={{ boxShadow: "0 2px 8px rgba(0,0,0,0.05)" }}
      transition={{ duration: 0.15 }}
      className="bg-[var(--color-paper)] border border-[var(--color-line)] rounded-[8px] p-[20px]"
      style={{ borderLeft: `3px solid ${borderColor[status]}` }}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-4 mb-[12px]">
        <h3 className="text-heading text-[var(--color-ink)] break-all">{originalFilename}</h3>
        <StatusBadge status={status} />
      </div>

      {/* Signer + timestamp */}
      <div className="flex flex-col gap-[4px] mb-[16px]">
        {signer && (
          <p className="text-body-sm text-[var(--color-ink-muted)]">
            Signer: {signer.display_name ? `${signer.display_name} (${signer.identifier})` : signer.identifier}
          </p>
        )}
        <p className="text-mono text-[var(--color-ink-muted)]">
          {refreshFailed ? "Refresh failed. " : ""}
          Last updated {formatDistanceToNow(updatedAt)} ago
        </p>
        {signer?.signer_url && status === "pending" && (
          <a
            href={signer.signer_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-body-sm text-[var(--color-signature)] hover:underline mt-[4px]"
          >
            Open signing link
          </a>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <p className="text-mono text-[var(--color-ink-muted)] text-[11px]">{signatureRequestId.slice(0, 8)}…</p>
        <div className="flex gap-[8px]">
          <Button variant="secondary" onClick={onRefresh} loading={refreshing} disabled={refreshing}>
            Refresh status
          </Button>
          {status === "signed" && (
            <Button variant="primary" onClick={onDownload} loading={downloading} disabled={downloading}>
              Download signed PDF
            </Button>
          )}
        </div>
      </div>
    </motion.div>
  );
}
