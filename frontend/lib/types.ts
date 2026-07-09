/**
 * Shared TypeScript types matching backend Pydantic schemas.
 */

export type SignatureStatus = "pending" | "signed" | "expired" | "failed" | "no_request";

export interface SignerInfo {
  identifier: string;
  display_name?: string | null;
  status: string;
  signer_url: string;
  signed_at?: string | null;
}

export interface UploadContractResponse {
  document_id: string;
  setu_document_id: string;
  original_filename: string;
  file_size_bytes: number;
  uploaded_at: string;
  signature_request_id: string;
  setu_signature_id: string;
  status: SignatureStatus;
  signer_url: string;
}

export interface SignatureStatusResponse {
  signature_request_id: string;
  setu_signature_id: string;
  document_id: string;
  original_filename: string;
  status: SignatureStatus;
  signers: SignerInfo[];
  updated_at: string;
  refresh_failed: boolean;
  last_refreshed_at?: string | null;
}

export interface DocumentListItem {
  document_id: string;
  original_filename: string;
  uploaded_at: string;
  signature_request_id?: string | null;
  setu_signature_id?: string | null;
  status: SignatureStatus;
  updated_at?: string | null;
  signers: SignerInfo[];
}
