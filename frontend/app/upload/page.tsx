"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import UploadDropzone from "@/components/UploadDropzone";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import StatusBadge from "@/components/StatusBadge";
import { uploadContract } from "@/lib/api";
import { UploadContractResponse } from "@/lib/types";

type Step = "select" | "details" | "uploading" | "success";

export default function UploadPage() {
  const { getToken } = useAuth();

  const [step, setStep] = useState<Step>("select");
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [signerIdentifier, setSignerIdentifier] = useState("");
  const [signerDisplayName, setSignerDisplayName] = useState("");
  const [signerError, setSignerError] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [result, setResult] = useState<UploadContractResponse | null>(null);
  const [copied, setCopied] = useState(false);

  function handleFileSelected(f: File) {
    setFileError(null);
    // Client-side fast check before sending to server
    if (!f.name.toLowerCase().endsWith(".pdf") && f.type !== "application/pdf") {
      setFileError("This file is not a valid PDF. Please upload a PDF document.");
      return;
    }
    if (f.size > 10 * 1024 * 1024) {
      const mb = (f.size / (1024 * 1024)).toFixed(1);
      setFileError(`This file is ${mb}MB — the limit is 10MB. Choose a smaller PDF.`);
      return;
    }
    setFile(f);
    setStep("details");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSignerError(null);
    setUploadError(null);

    // Validate mobile number
    const cleaned = signerIdentifier.replace(/[\s-]/g, "");
    if (!/^[6-9]\d{9}$/.test(cleaned)) {
      setSignerError("Please enter a valid 10-digit Aadhaar-linked mobile number.");
      return;
    }

    if (!file) return;

    setStep("uploading");

    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated. Please sign in.");

      const data = await uploadContract(
        token,
        file,
        cleaned,
        signerDisplayName || undefined
      );

      setResult(data);
      setStep("success");
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Upload failed. Please try again.");
      setStep("details");
    } finally {
    }
  }

  async function copyLink() {
    if (!result?.signer_url) return;
    await navigator.clipboard.writeText(result.signer_url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <main className="min-h-screen py-[40px] px-[24px] lg:px-[40px]">
      <div className="max-w-[720px] mx-auto">
        {/* Header */}
        <div className="mb-[40px]">
          <Link
            href="/"
            className="text-body-sm text-[var(--color-ink-muted)] hover:text-[var(--color-ink)] mb-[16px] inline-block"
          >
            ← Back
          </Link>
          <h1 className="text-display-sm text-[var(--color-ink)]">Send a contract for signature</h1>
        </div>

        {/* Step: Select file */}
        {(step === "select" || step === "details") && (
          <>
            <div className="mb-[24px]">
              <UploadDropzone
                onFileSelected={handleFileSelected}
                disabled={step === "details"}
                error={fileError || undefined}
              />
              {file && step === "details" && (
                <div className="mt-[8px] flex items-center justify-between">
                  <p className="text-body-sm text-[var(--color-ink-muted)]">
                    {file.name} ({(file.size / 1024).toFixed(0)} KB)
                  </p>
                  <button
                    onClick={() => { setFile(null); setStep("select"); }}
                    className="text-body-sm text-[var(--color-status-expired)] hover:underline"
                  >
                    Remove
                  </button>
                </div>
              )}
            </div>

            {/* Step: Signer details form */}
            {step === "details" && (
              <form onSubmit={handleSubmit} className="flex flex-col gap-[20px]">
                <div className="border-t border-[var(--color-line)] pt-[24px]">
                  <h2 className="text-heading text-[var(--color-ink)] mb-[20px]">Signer details</h2>
                  <div className="flex flex-col gap-[16px]">
                    <Input
                      label="Aadhaar-linked mobile number"
                      type="tel"
                      placeholder="98765 43210"
                      value={signerIdentifier}
                      onChange={(e) => { setSignerIdentifier(e.target.value); setSignerError(null); }}
                      error={signerError || undefined}
                      required
                    />
                    <Input
                      label="Signer's name (optional)"
                      type="text"
                      placeholder="Full name as on Aadhaar"
                      value={signerDisplayName}
                      onChange={(e) => setSignerDisplayName(e.target.value)}
                      hint="If provided, Setu will validate this against Aadhaar OTP verification."
                    />
                  </div>
                </div>

                {uploadError && (
                  <p className="text-body-sm text-[var(--color-status-expired)]">{uploadError}</p>
                )}

                <div className="flex gap-[8px] justify-end">
                  <Button variant="secondary" type="button" onClick={() => { setFile(null); setStep("select"); }}>
                    Cancel
                  </Button>
                  <Button variant="primary" type="submit">
                    Send for signature
                  </Button>
                </div>
              </form>
            )}
          </>
        )}

        {/* Step: Uploading */}
        {step === "uploading" && (
          <div className="py-[64px] text-center">
            <div className="w-8 h-8 border-2 border-[var(--color-signature)] border-t-transparent rounded-full animate-spin mx-auto mb-[16px]" />
            <p className="text-body text-[var(--color-ink-muted)]">Uploading and creating signature request…</p>
          </div>
        )}

        {/* Step: Success */}
        {step === "success" && result && (
          <div className="border border-[var(--color-line)] rounded-[8px] p-[24px]"
               style={{ borderLeft: "3px solid var(--color-status-signed)" }}>
            <div className="flex items-center justify-between mb-[16px]">
              <h2 className="text-heading text-[var(--color-ink)]">{result.original_filename}</h2>
              <StatusBadge status={result.status} />
            </div>

            <div className="flex flex-col gap-[8px] mb-[24px]">
              <p className="text-body-sm text-[var(--color-ink-muted)]">
                Signature request created. Share the signing link with the signer.
              </p>
              <div className="flex items-center gap-[8px] mt-[4px]">
                <a
                  href={result.signer_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-body-sm text-[var(--color-signature)] hover:underline break-all flex-1"
                >
                  {result.signer_url}
                </a>
                <button
                  onClick={copyLink}
                  className="text-caption text-[var(--color-ink-muted)] hover:text-[var(--color-ink)] whitespace-nowrap border border-[var(--color-line)] rounded-[4px] px-[8px] py-[4px] transition-colors"
                >
                  {copied ? "Copied" : "Copy link"}
                </button>
              </div>
              <div className="flex flex-col gap-[4px] mt-[8px]">
                <p className="text-mono text-[var(--color-ink-muted)]">
                  Request ID: {result.signature_request_id}
                </p>
              </div>
            </div>

            <div className="flex gap-[8px]">
              <Button variant="secondary" onClick={() => { setFile(null); setResult(null); setStep("select"); setSignerIdentifier(""); setSignerDisplayName(""); }}>
                Send another
              </Button>
              <Link href="/status">
                <Button variant="primary">View status</Button>
              </Link>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
