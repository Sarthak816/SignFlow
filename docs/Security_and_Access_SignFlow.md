# Security and Access Document: SignFlow

**Author:** Sarthak Pal
**Status:** Draft v1.0
**Companion docs:** PRD_SignFlow.md, Technical_Architecture_SignFlow.md
**Last updated:** July 8, 2026
**Audience note:** written so a non-technical founder can read it end to end and understand exactly what's protected, who can do what, and what happens when something goes wrong.

---

## 1. Authentication: What Fits This App and Why

**Recommendation: Email + magic link (passwordless) authentication for internal users, via a hosted provider like Clerk or Supabase Auth. No login at all for signers.**

Here's the reasoning, in plain terms:

- **Internal users** (the person sending documents — Priya, Rohan) need to log in, but they're a small, known group. A full password system means you now own password resets, password strength rules, and the risk of leaked password databases. A magic link (click a link in your email to log in) removes passwords entirely — nothing to leak, nothing to reset, nothing to brute-force.
- **Signers** (the person receiving a document to sign) should **never** need a SignFlow account. They receive a unique, single-purpose link and use it to sign through Setu's own hosted flow. Making them create an account would kill the whole point of the product — the friction of "get this signed" is exactly what SignFlow removes. Their identity is verified by Setu's Aadhaar eSign process itself, not by SignFlow.
- **Don't build this yourself.** Authentication is one of the few areas where "roll your own" is genuinely risky even for a skilled engineer — a hosted provider has already been through the security review, penetration testing, and edge-case hardening that a v1 product doesn't have time for.

**In short:** two very different kinds of "access" exist in this product — logged-in senders, and link-holding signers — and they should be treated as fundamentally different, not squeezed into one login system.

---

## 2. User Roles: What Each Role Can and Cannot Do

Even though MVP is single-user, defining roles now avoids a painful redesign the moment you add a second team member.

### Role: **Owner**
*The person who created the SignFlow account for their organization.*

**Can:**
- Upload documents and create signature requests
- View status and download signed documents for every request in their organization
- Invite additional team members (once multi-user exists — see PRD, deferred)
- View the full history of all documents ever sent

**Cannot:**
- Access another organization's documents, under any circumstance
- See Setu credentials or any backend secrets — these are never exposed to any role, including the Owner

### Role: **Team Member** *(future role, not needed until multi-user ships)*
*A colleague added by the Owner.*

**Can:**
- Upload documents and create signature requests
- View status and download signed documents for requests **they created**

**Cannot:**
- View or download documents created by other team members, unless the Owner explicitly enables shared visibility
- Invite other team members
- Delete another team member's documents

### Role: **Signer** *(external, no account)*
*The person asked to sign a document. Identified only by a unique link, not a login.*

**Can:**
- Open their unique signing link and complete the signing flow through Setu
- View only the one document their link points to

**Cannot:**
- See any other document in the system, past or present
- See who else has been sent documents
- Re-use their link after it has been signed or has expired
- Access anything by guessing or modifying the link — links must be unguessable (see Section 3)

### Role: **System / Backend Service**
*Not a human — this is SignFlow's own backend calling Setu.*

**Can:**
- Read and write Setu credentials (the only place in the entire system these ever live)
- Create, read, and update rows in all three database tables

**Cannot:**
- Be reachable directly by the frontend for anything Setu-related — every Setu interaction is proxied, never direct (this is already a hard requirement from the architecture doc, and it's a security boundary as much as a design one)

---

## 3. Row-Level Security Rules (Database Access Rules)

Row-level security means: **even if two different organizations' data lives in the same table, one organization's queries should be structurally incapable of returning another organization's rows.**

Plain-English rules for each table:

### `documents`
- Every row belongs to exactly one organization (via an `organization_id` field, added once multi-user exists).
- A query for documents must always be filtered by "documents belonging to the organization of the currently logged-in user." There should be no code path where documents are fetched without this filter.
- A Team Member can only see documents where they are the uploader, unless the Owner has turned on shared visibility for the organization.

### `signature_requests`
- Same organization-scoping rule as `documents` — inherited through the `document_id` relationship.
- The **only** way to reach a specific `signature_request` row without being logged in is through its unique signer link/token (see below) — never through a guessable numeric ID in a URL.

### `signers`
- A signer can only ever see the one row that corresponds to their own link/token. There is no "list signers" view exposed to anyone but the Owner/Team Member who sent the request.
- A signer's mobile number should never be exposed in any response to another signer, even indirectly (e.g., in error messages that leak "this number already has a pending request").

### The golden rule underneath all three
**Every signing link should use a long, random, unguessable token (not a sequential ID like `/status/1`, `/status/2`) as the thing that grants access — because if IDs are guessable, someone could type `/status/2` and view a stranger's contract without ever being a "user" in the system at all.** This is arguably the single most important row-level security rule in this entire document, because it's the one rule that protects data from someone who was never supposed to be logged in in the first place.

---

## 4. Error Handling Guide (Major Failure Points)

For each point where something can go wrong, here's what should happen — described in terms of what the user sees and why.

### Upload failure
**What can go wrong:** wrong file type, file too large, upload interrupted by a network drop.
**What should happen:** the user sees a specific, human message ("This file is 18MB — the limit is 10MB," not "Upload failed"). The file is validated *before* any Setu API call is made, so a bad upload never wastes a Setu API request or creates a half-finished database row.

### Setu API is down or times out
**What can go wrong:** Setu's service is temporarily unavailable, or a request takes too long.
**What should happen:** the backend sets a reasonable timeout (e.g., 15 seconds) rather than hanging indefinitely. The user sees "We couldn't reach our signing partner right now — please try again in a few minutes," and no document is left in a confusing half-created state. The attempted request should be safely retryable rather than creating a duplicate.

### Signature request creation fails after a successful upload
**What can go wrong:** the document uploads fine, but creating the signature request fails.
**What should happen:** the document record still exists (so nothing is silently lost) and its status is clearly marked as "upload succeeded, signature request failed" rather than left ambiguous. The user gets a clear retry option rather than having to re-upload from scratch.

### Signer's link has expired
**What can go wrong:** a signer opens a link days after it was sent, and Setu has expired it.
**What should happen:** the signer sees a plain message explaining the link expired and who to contact (the original sender), not a raw error or broken page. The sender's status page reflects "Expired," not a stale "Pending."

### Status check fails
**What can go wrong:** the "check status" call to Setu fails or times out.
**What should happen:** the UI shows the **last known status** with a note like "last updated 3 minutes ago — refresh failed," rather than showing a blank or broken screen. Never show nothing; show the most recent good data you have.

### Download requested before signing is complete
**What can go wrong:** someone clicks download before the document is actually signed.
**What should happen:** the download button simply shouldn't be clickable/visible until status is "Signed" — this is a case where the best error handling is preventing the error state from being reachable at all.

### Duplicate signature requests for the same document
**What can go wrong:** a user double-clicks "send" or refreshes mid-request and accidentally creates two signature requests for the same document.
**What should happen:** the backend should treat this as an unsafe action to repeat blindly (an "idempotency" concern) — either disable the button immediately on click, or check for an existing pending request for that document before creating a new one.

### Database is temporarily unreachable
**What can go wrong:** the database itself has a brief outage.
**What should happen:** the user sees a generic "something went wrong on our end, please try again shortly" message. Critically, **no raw database error, stack trace, or technical detail should ever reach the user's screen** — that's both bad UX and a security risk, since error details can leak information about your system's internals.

---

## 5. Edge Cases to Handle Before Launch

- **Signer opens the link twice** — the second visit should show current status ("already signed" or "still pending"), not let them attempt to sign again.
- **Signer declines or abandons the signing flow partway through** — status should reflect this accurately rather than sitting at "Pending" forever with no explanation.
- **Two signature requests are created for the same document in quick succession** (double-click, slow network, retry) — only one should be treated as active.
- **A file is renamed to `.pdf` but isn't actually a valid PDF** — validate the file's actual content type on the backend, not just its file extension, since extensions are trivially fake.
- **Signer's mobile number is mistyped by the sender** — there's no way for SignFlow to catch this automatically (Setu is Aadhaar OTP-based, so signer identity is by phone number, not email), but the sender should have an easy way to cancel a request and send a corrected one, rather than being stuck.
- **The same document is uploaded twice by mistake** — not a security issue, but a UX one worth deciding on: either allow it freely (simplest for MVP) or detect likely duplicates and warn the user.
- **A signer's link is forwarded to someone else** (accidentally or otherwise) — because Setu's own identity verification (Aadhaar eSign) happens at signing time, the actual legal signature is still tied to the real signer's identity, not just whoever clicked the link. Worth stating clearly in your README so this isn't mistaken for a SignFlow security gap.
- **Sandbox vs. production Setu credentials get mixed up** — worth a startup check that fails loudly (not silently) if `SETU_BASE_URL` and the credential type don't match, so you never accidentally send a real contract through sandbox or vice versa.
- **Someone tries to guess another signer's link by modifying a URL** — this is exactly why Section 3's "unguessable token" rule exists; test this explicitly before launch by trying to access a document with a slightly modified link.
- **Setu sends a status update slower than the user expects** — if you're on manual refresh (MVP) rather than webhooks, make sure the UI never implies real-time accuracy it doesn't have; a small "as of [time]" label avoids false confidence.
- **A large number of documents pile up in one account** — even in MVP, the status/history page should handle pagination or at least not visibly break once someone has 50+ documents.
- **Browser back button after a completed upload** — navigating back shouldn't allow re-submitting the same upload form and creating a duplicate request.

---

## 6. One-Paragraph Summary for a Founder

SignFlow keeps three kinds of access clearly separate: people who log in to send documents (protected by passwordless email login, not passwords), people who receive a document to sign (protected only by an unguessable link — no account needed), and the backend service itself (the only place your Setu credentials ever exist). The single most important rule in this whole document is that signing links must be unguessable, because that link *is* the security boundary for every signer who will ever use this product. Everything else — error messages, retry behavior, edge cases — exists to make sure that when something breaks, it breaks safely and visibly instead of quietly and dangerously.
