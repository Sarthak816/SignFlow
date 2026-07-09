"use client";

import Link from "next/link";
import { useAuth, SignInButton, SignOutButton } from "@clerk/nextjs";

export default function LandingPage() {
  const { isSignedIn, isLoaded } = useAuth();

  return (
    <main className="min-h-screen flex flex-col">
      {/* Nav */}
      <nav className="border-b border-[var(--color-line)] px-[24px] lg:px-[40px] py-[16px] flex items-center justify-between">
        <span className="text-heading text-[var(--color-ink)]">SignFlow</span>
        {isLoaded && isSignedIn && (
          <div className="flex gap-[8px] items-center">
            <Link href="/status" className="text-body-sm text-[var(--color-ink-muted)] hover:text-[var(--color-ink)] mr-[8px]">
              Document status
            </Link>
            <SignOutButton>
              <button className="text-body-sm text-[var(--color-ink-muted)] hover:text-[var(--color-ink)]">
                Sign out
              </button>
            </SignOutButton>
          </div>
        )}
      </nav>

      {/* Hero */}
      <section className="flex-1 flex items-center justify-center px-[24px] lg:px-[40px]">
        <div className="max-w-[960px] w-full">
          <h1 className="text-display-lg text-[var(--color-ink)] mb-[24px] max-w-[640px]">
            Get contracts signed.<br />Track every step.
          </h1>
          <p className="text-body text-[var(--color-ink-muted)] mb-[40px] max-w-[480px]">
            Upload a PDF, send it for Aadhaar-based e-signature, and download the signed document. Full status trail included, no chasing required.
          </p>

          {!isLoaded ? null : isSignedIn ? (
            <div className="flex gap-[12px] flex-wrap">
              <Link href="/upload">
                <button className="inline-flex items-center justify-center rounded-[6px] px-[18px] py-[10px] text-[14px] font-semibold bg-[var(--color-signature)] text-white hover:bg-[var(--color-signature-hover)] transition-colors">
                  Send a contract for signature
                </button>
              </Link>
              <Link href="/status">
                <button className="inline-flex items-center justify-center rounded-[6px] px-[18px] py-[10px] text-[14px] font-semibold bg-[var(--color-paper)] text-[var(--color-ink)] border border-[var(--color-line)] hover:bg-[var(--color-line)] transition-colors">
                  View document status
                </button>
              </Link>
            </div>
          ) : (
            <SignInButton mode="modal">
              <button className="inline-flex items-center justify-center rounded-[6px] px-[18px] py-[10px] text-[14px] font-semibold bg-[var(--color-signature)] text-white hover:bg-[var(--color-signature-hover)] transition-colors">
                Sign in to get started
              </button>
            </SignInButton>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[var(--color-line)] px-[24px] lg:px-[40px] py-[16px]">
        <p className="text-body-sm text-[var(--color-ink-muted)]">
          Powered by Setu Aadhaar eSign
        </p>
      </footer>
    </main>
  );
}
