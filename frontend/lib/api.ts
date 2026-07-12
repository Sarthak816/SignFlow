/**
 * Typed fetch wrapper for all SignFlow backend API calls.
 * Attaches Clerk session token to every request automatically.
 */

import { UploadContractResponse, SignatureStatusResponse, DocumentListItem } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function apiFetch<T>(
  path: string,
  token: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${token}`,
      "ngrok-skip-browser-warning": "true",
    },
  });

  if (!res.ok) {
    let detail = `Request failed: ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail || body.error || detail;
    } catch {}
    throw new Error(detail);
  }

  return res.json();
}

export async function uploadContract(
  token: string,
  file: File,
  signerIdentifier: string,
  signerDisplayName?: string
): Promise<UploadContractResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("signer_identifier", signerIdentifier);
  if (signerDisplayName) formData.append("signer_display_name", signerDisplayName);

  const res = await fetch(`${BASE}/api/upload-contract`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });

  if (!res.ok) {
    let detail = `Upload failed: ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail || body.error || detail;
    } catch {}
    throw new Error(detail);
  }

  return res.json();
}

export async function getSignatureStatus(
  token: string,
  signatureRequestId: string
): Promise<SignatureStatusResponse> {
  return apiFetch<SignatureStatusResponse>(
    `/api/signature-status/${signatureRequestId}`,
    token
  );
}

export async function getDocuments(token: string): Promise<DocumentListItem[]> {
  return apiFetch<DocumentListItem[]>("/api/documents", token);
}

export async function downloadSignedDocument(
  token: string,
  signatureRequestId: string
): Promise<Blob> {
  const res = await fetch(`${BASE}/api/download/${signatureRequestId}`, {
    headers: { 
      Authorization: `Bearer ${token}`,
      "ngrok-skip-browser-warning": "true",
    },
  });

  if (!res.ok) {
    let detail = `Download failed: ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail || body.error || detail;
    } catch {}
    throw new Error(detail);
  }

  return res.blob();
}
