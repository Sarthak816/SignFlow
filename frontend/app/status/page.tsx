"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import DocumentCard from "@/components/DocumentCard";
import { getDocuments, getSignatureStatus, downloadSignedDocument } from "@/lib/api";
import { downloadBlob } from "@/lib/utils";
import { DocumentListItem } from "@/lib/types";

export default function StatusPage() {
  const { getToken } = useAuth();
  const [documents, setDocuments] = useState<DocumentListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState<Record<string, boolean>>({});
  const [downloading, setDownloading] = useState<Record<string, boolean>>({});

  async function loadDocuments() {
    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      const docs = await getDocuments(token);
      setDocuments(docs);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load documents");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDocuments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Real-time polling for pending signature requests
  useEffect(() => {
    const pendingDocs = documents.filter(
      (doc) => doc.status === "pending" && doc.signature_request_id
    );
    if (pendingDocs.length === 0) return;

    const interval = setInterval(() => {
      pendingDocs.forEach((doc) => {
        handleRefresh(doc.signature_request_id!);
      });
    }, 8000); // Poll every 8 seconds

    return () => clearInterval(interval);
  }, [documents]);

  async function handleRefresh(signatureRequestId: string) {
    setRefreshing((prev) => ({ ...prev, [signatureRequestId]: true }));
    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      const updated = await getSignatureStatus(token, signatureRequestId);

      // Update that specific document in the list
      setDocuments((prev) =>
        prev.map((doc) =>
          doc.signature_request_id === signatureRequestId
            ? {
                ...doc,
                status: updated.status,
                updated_at: updated.updated_at,
                signers: updated.signers,
              }
            : doc
        )
      );
    } catch (err) {
      console.error("Refresh failed:", err);
    } finally {
      setRefreshing((prev) => ({ ...prev, [signatureRequestId]: false }));
    }
  }

  async function handleDownload(signatureRequestId: string, filename: string) {
    setDownloading((prev) => ({ ...prev, [signatureRequestId]: true }));
    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      const blob = await downloadSignedDocument(token, signatureRequestId);
      downloadBlob(blob, `signed-${filename}`);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Download failed");
    } finally {
      setDownloading((prev) => ({ ...prev, [signatureRequestId]: false }));
    }
  }

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <p className="text-body text-[var(--color-ink-muted)]">Loading documents…</p>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-body text-[var(--color-status-expired)] mb-4">{error}</p>
          <button
            onClick={loadDocuments}
            className="text-body-sm text-[var(--color-signature)] hover:underline"
          >
            Try again
          </button>
        </div>
      </main>
    );
  }

  const documentsWithRequests = documents.filter((d) => d.signature_request_id);

  return (
    <main className="min-h-screen py-[40px] px-[24px] lg:px-[40px]">
      <div className="max-w-[720px] mx-auto">
        <h1 className="text-display-sm text-[var(--color-ink)] mb-[24px]">Document Status</h1>

        {documentsWithRequests.length === 0 ? (
          <div className="text-center py-[64px]">
            <p className="text-body text-[var(--color-ink-muted)]">
              No documents yet. Upload a contract to send it for signature.
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-[16px]">
            {documentsWithRequests.map((doc) => (
              <DocumentCard
                key={doc.signature_request_id}
                signatureRequestId={doc.signature_request_id!}
                originalFilename={doc.original_filename}
                status={doc.status}
                signers={doc.signers}
                updatedAt={doc.updated_at || doc.uploaded_at}
                onRefresh={() => handleRefresh(doc.signature_request_id!)}
                onDownload={() => handleDownload(doc.signature_request_id!, doc.original_filename)}
                refreshing={refreshing[doc.signature_request_id!]}
                downloading={downloading[doc.signature_request_id!]}
              />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
