"use client";

import Link from "next/link";
import { useAuth, SignInButton, SignOutButton } from "@clerk/nextjs";

export default function LandingPage() {
  const { isSignedIn, isLoaded } = useAuth();

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8">
      <h1 className="text-4xl font-bold mb-4">SignFlow</h1>
      <p className="text-lg text-gray-600 mb-8 text-center max-w-xl">
        Upload a PDF, send it for legally valid e-signature, track status in
        real time, and download the signed document.
      </p>

      {!isLoaded ? null : isSignedIn ? (
        <div className="flex gap-4">
          <Link
            href="/upload"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Upload a contract
          </Link>
          <SignOutButton>
            <button className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition">
              Sign out
            </button>
          </SignOutButton>
        </div>
      ) : (
        <SignInButton mode="modal">
          <button className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
            Sign in to get started
          </button>
        </SignInButton>
      )}
    </main>
  );
}
