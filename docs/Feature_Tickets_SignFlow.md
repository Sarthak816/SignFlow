# Feature Ticket List: SignFlow

**Author:** Sarthak Pal
**Status:** v1.0 — reconciled against PRD_SignFlow.md, Technical_Architecture_SignFlow.md, Security_and_Access_SignFlow.md, Frontend_Specification_SignFlow.md
**Last updated:** July 8, 2026

**How to use this file:** each ticket is self-contained and ends with an **AI Prompt** block — paste that block directly into Kiro, Antigravity, Claude Code, or Cursor as the instruction for that one feature. Build and commit tickets **in order**; later tickets assume earlier ones exist. Do not skip ahead even if a later ticket looks easy — the dependency chain is deliberate.

**Reconciliation note:** this ticket list assumes the MVP now includes single-account Clerk auth (see the auth reconciliation made to Technical_Architecture_SignFlow.md, Section 1) — every document is scoped to one logged-in Owner from day one, even though team accounts stay deferred.

---

## Priority key
- 🔴 **Must-have** — required for a working MVP submission
- 🟡 **Should-have** — strengthens the submission, not launch-blocking
- 🟢 **Nice-to-have** — explicitly deferred per the PRD, build only if time remains

---

## Phase 0 — Project Setup

### T0.1 — Repository & Project Scaffold
🔴 Must-have | **Dependencies:** none

**Description:** Set up the monorepo structure exactly as defined in Technical_Architecture_SignFlow.md, Section 2 — a `backend/` FastAPI project and a `frontend/` Next.js (TypeScript) project, each with their own dependency file, plus a top-level `README.md` and `docs/` folder holding the four spec documents.

**Acceptance criteria:**
- [ ] `backend/` runs a bare FastAPI app on `uvicorn app.main:app --reload` and returns a 200 on a `/health` route
- [ ] `frontend/` runs `npm run dev` and shows a default Next.js page
- [ ] Folder structure matches Technical_Architecture_SignFlow.md, Section 2, exactly
- [ ] `.env.example` exists in both `backend/` and `frontend/` listing every variable from Technical_Architecture_SignFlow.md, Section 4, with no real values
- [ ] `.gitignore` excludes `.env`, `.env.local`, `node_modules/`, `__pycache__/`, and any local upload storage folder
- [ ] First commit made and pushed to a new GitHub repo

**AI Prompt:**
```
Set up a monorepo with a `backend/` FastAPI (Python) project and a `frontend/` Next.js (TypeScript) project. Follow this exact folder structure: [paste Technical_Architecture_SignFlow.md Section 2]. Backend needs a `/health` route returning 200. Frontend should run with `npm run dev` on the default Next.js starter page. Create `.env.example` files in both folders listing these variables with empty values: [paste Technical_Architecture_SignFlow.md Section 4 variable names]. Add a `.gitignore` excluding env files, node_modules, __pycache__, and local file storage. Do not implement any feature logic yet — this ticket is scaffolding only.
```

---

### T0.2 — Database Setup & Migrations
🔴 Must-have | **Dependencies:** T0.1

**Description:** Connect the backend to Postgres via SQLAlchemy, set up Alembic, and create the initial migration for all three tables exactly as defined in Technical_Architecture_SignFlow.md, Section 3 (including the `owner_id` field on `documents`).

**Acceptance criteria:**
- [ ] `DATABASE_URL` is read from environment config, not hardcoded
- [ ] SQLAlchemy models exist for `documents`, `signature_requests`, `signers` matching the schema exactly, including field types and foreign keys
- [ ] Alembic is initialized and `alembic upgrade head` creates all three tables with correct relationships
- [ ] Running the migration twice doesn't error (idempotent)
- [ ] Committed and pushed

**AI Prompt:**
```
In the backend/ FastAPI project, set up SQLAlchemy with a Postgres connection using DATABASE_URL from environment config. Create three models: documents, signature_requests, and signers, matching this exact schema: [paste Technical_Architecture_SignFlow.md Section 3 in full, including the owner_id field]. Set up Alembic for migrations and generate the initial migration that creates all three tables with the foreign key relationships described (documents 1-to-many signature_requests, signature_requests 1-to-many signers). Do not build any API routes yet — this ticket is database setup only.
```

---

### T0.3 — Clerk Auth Integration (Single Owner Account)
🔴 Must-have | **Dependencies:** T0.1

**Description:** Wire up Clerk for passwordless magic-link login on the frontend, and Clerk's backend SDK to verify sessions on protected API routes. This is single-account auth — no invite flow, no roles UI, just "logged in or not" for now.

**Acceptance criteria:**
- [ ] A user can enter their email on the frontend and receive a magic link that logs them in
- [ ] A logged-in user's session persists across page reloads
- [ ] The backend has a reusable dependency/middleware that verifies a Clerk session token and returns the `userId`, rejecting unauthenticated requests with a 401
- [ ] No password field exists anywhere in the app
- [ ] Committed and pushed

**AI Prompt:**
```
Integrate Clerk for passwordless magic-link authentication. On the frontend (Next.js), add Clerk's sign-in flow so a user can log in with just their email via a magic link, and protect all app routes except the landing page behind this login. On the backend (FastAPI), add a reusable dependency that verifies the Clerk session token sent from the frontend and returns the authenticated userId, rejecting any request without a valid session with a 401. Do not build a signup/invite flow or any role selection UI — this is single-account auth only.
```

---

## Phase 1 — Core Upload & Setu Integration

### T1.1 — Setu API Client Service
🔴 Must-have | **Dependencies:** T0.2

**Description:** Build the backend service that wraps all four Setu API calls, exactly as specified in Frontend_Specification_SignFlow.md, Section 7.1. This is the *only* file in the entire codebase allowed to reference Setu credentials.

**Acceptance criteria:**
- [ ] A `services/setu_client.py` module exists with four functions: `upload_document`, `create_signature_request`, `get_signature_status`, `download_document`
- [ ] Credentials (`x-client-id`, `x-client-secret`, `x-product-instance-id`) are read from environment config and attached as headers inside this file only — confirmed by grepping the rest of the codebase for these variable names and finding zero other matches
- [ ] Every call has a 15-second timeout and raises a clear, catchable error on timeout or non-2xx response (per Security_and_Access_SignFlow.md, Section 4, "Setu API is down or times out")
- [ ] Unit tests mock the Setu HTTP calls and verify each function's request shape and response parsing
- [ ] Committed and pushed

**AI Prompt:**
```
Create a backend service module services/setu_client.py that wraps four Setu API calls, matching the real shapes documented in Frontend_Specification_SignFlow.md Section 7.1: upload_document (POST /api/documents, multipart with a `payload` field of {"name": ...} and a `files` field for the PDF, returns { id, name } — store `id` as our documentId), create_signature_request (POST /api/signature with documentId, redirectUrl, and a signers list where each signer has an `identifier` — an Aadhaar-linked mobile number, not an email — plus optional displayName/birthYear, returns { id (the signatureId), signers: [{ id, url, status }] } with one url per signer), get_signature_status (GET /api/signature/:id, returns Setu's real status enum sign_initiated/sign_pending/sign_in_progress/sign_complete at the request level and pending/in_progress/signed per signer), and download_document (GET /api/signature/:id/download/ — note this uses the signatureId, not documentId — returns { downloadUrl, validUpto }, a pre-signed URL your function should then fetch itself and return the binary content of). Read SETU_CLIENT_ID, SETU_CLIENT_SECRET, SETU_PRODUCT_INSTANCE_ID, and SETU_BASE_URL from environment config and attach them as request headers — these credentials must not appear anywhere else in the codebase. Every call needs a 15-second timeout and should raise a specific, catchable exception on timeout or failure so calling code can show a clear error message. Write unit tests that mock the HTTP layer and verify request/response handling for all four functions.
```

---

### T1.2 — Upload Contract Endpoint
🔴 Must-have | **Dependencies:** T1.1, T0.3

**Description:** Build `POST /api/upload-contract` — validates the file, saves it via the storage abstraction, calls Setu to upload it, and writes the `documents` row (scoped to the logged-in owner).

**Acceptance criteria:**
- [ ] Route requires authentication (rejects with 401 if no valid session)
- [ ] Rejects non-PDF files based on actual file content, not just the `.pdf` extension (per Security_and_Access_SignFlow.md, Section 5, "file renamed to `.pdf`")
- [ ] Rejects files over the `MAX_UPLOAD_SIZE_MB` limit with a specific error message stating the actual limit
- [ ] On success, saves the file via `services/storage.py`, calls `setu_client.upload_document`, and creates a `documents` row with `owner_id` set to the authenticated user
- [ ] On Setu failure after a successful file save, the document row is still created with a status reflecting the partial failure (per Security_and_Access_SignFlow.md, Section 4)
- [ ] Returns `{ documentId, setuDocumentId, filename, uploadedAt }`
- [ ] Committed and pushed

**AI Prompt:**
```
Build a POST /api/upload-contract endpoint in the FastAPI backend, protected by the Clerk auth dependency from T0.3. Accept a multipart PDF upload. Validate the file is actually a PDF by checking its content/magic bytes, not just its extension, and reject it with a clear error if not. Validate file size against MAX_UPLOAD_SIZE_MB from environment config and reject oversized files with a message stating the actual limit. On a valid file: save it using a storage.py abstraction (local disk for now, behind an interface that could later swap to S3), call the setu_client.upload_document function from T1.1, and create a documents row with owner_id set to the authenticated user's ID, storing the returned Setu documentId, filename, file size, and upload timestamp. If the Setu call fails after the file is already saved, still create the documents row but mark it with a status indicating the Setu upload failed, so nothing is silently lost. Return the created document's data as JSON.
```

---

### T1.3 — Signature Request Creation (Backend)
🔴 Must-have | **Dependencies:** T1.2

**Description:** Extend the upload flow (or add a follow-up endpoint) that takes a signer's Aadhaar-linked mobile number for an uploaded document, calls Setu to create the signature request, and writes `signature_requests` and `signers` rows.

**Acceptance criteria:**
- [ ] Accepts a `documentId` and a single signer's `identifier` (Aadhaar-linked mobile number) + optional `displayName`
- [ ] Validates the identifier is a plausible mobile number format before calling Setu
- [ ] Calls `setu_client.create_signature_request`, storing the returned `signatureId` and `signerUrl`
- [ ] Creates one `signature_requests` row (status `pending`) and one `signers` row linked to it
- [ ] If a `signature_requests` row already exists for this `documentId` with status `pending`, returns the existing one instead of creating a duplicate (per Security_and_Access_SignFlow.md, Section 4, "Duplicate signature requests")
- [ ] Returns `{ signatureId, signerUrl, status }`
- [ ] Committed and pushed

**AI Prompt:**
```
Add an endpoint (or extend upload-contract) that accepts a documentId and a signer's identifier (an Aadhaar-linked mobile number, plus optional displayName), validates the identifier looks like a plausible mobile number, and calls the setu_client.create_signature_request function from T1.1. Store the returned signatureId on the signature_requests row (status "pending", mapped from Setu's sign_initiated), and create a linked signers row storing the signer's Setu-assigned id, their identifier, displayName, and their individual signer_url (each signer gets their own signing link from Setu, not one shared link). Before creating a new signature_requests row, check whether a pending one already exists for this documentId — if so, return that existing one instead of creating a duplicate, to prevent double-submission from a double-click or retry. Return the signatureId, the signer's url, and status as JSON.
```

---

### T1.4 — Upload Contract Page (Frontend)
🔴 Must-have | **Dependencies:** T1.3, T4.1, T4.2

**Description:** Build the Upload page per Frontend_Specification_SignFlow.md — dropzone, signer mobile number field, submit, and success state showing the signing link.

**Acceptance criteria:**
- [ ] Matches the dropzone spec exactly (dashed border, drag-over state, helper text) from Frontend_Specification_SignFlow.md, Section 3
- [ ] Shows upload progress while the file is uploading
- [ ] Shows the file-type/size error inline per the Input error-state spec, without a page reload
- [ ] After successful upload, shows a signer mobile number input (with an optional name field), then on submit calls the signature-request endpoint
- [ ] On success, displays the `documentId`, `signatureId`, `signerUrl`, and status in a card matching the Card component spec
- [ ] Button/state disables itself immediately on click to prevent double-submission (per Security_and_Access_SignFlow.md, Section 4)
- [ ] Committed and pushed

**AI Prompt:**
```
Build the Upload Contract page at frontend/app/upload/page.tsx using the design tokens and component specs from Frontend_Specification_SignFlow.md (dropzone with dashed border and drag-over state, error states on the input, card styling for results). Flow: user drags or selects a PDF, sees upload progress, and on success sees a signer mobile number field (Setu's eSign is Aadhaar OTP-based, so the signer is identified by phone number, not email) with an optional display name field. Submitting that calls the signature-request endpoint from T1.3. On success, show a result card with the documentId, signatureId, the signer's individual signing url (as a copyable link), and status "Pending". Disable the submit button immediately on click to prevent accidental double-submission. Handle and display file-type and file-size errors inline, matching the input error-state spec, without a page reload.
```

---

## Phase 2 — Status & Download

### T2.1 — Signature Status Endpoint
🔴 Must-have | **Dependencies:** T1.3

**Description:** Build `GET /api/signature-status/:id` — fetches the latest status from Setu and updates the local `signature_requests`/`signers` rows.

**Acceptance criteria:**
- [ ] Route requires authentication and only returns data for requests owned by the authenticated user (row-level security check)
- [ ] Calls `setu_client.get_signature_status`, updates local `status`, `updated_at`, and any `signers.signed_at` values
- [ ] If the Setu call fails, returns the **last known local status** with a flag/timestamp indicating the refresh failed, rather than erroring out entirely (per Security_and_Access_SignFlow.md, Section 4, "Status check fails")
- [ ] Uses the unguessable `signatureId`/token as the lookup key, never a sequential internal ID, in any URL exposed to a non-owner
- [ ] Committed and pushed

**AI Prompt:**
```
Build a GET /api/signature-status/:id endpoint, protected by Clerk auth, where :id is the Setu signatureId. First verify the signature_requests row belongs to the authenticated user (owner_id match) — return 404, not 403, if it belongs to someone else, so ownership isn't leaked. Call setu_client.get_signature_status, and update the local signature_requests row's status and updated_at, plus any signers.signed_at values that are now set. If the Setu call itself fails or times out, don't error the whole request — return the last known local status along with a flag indicating the live refresh failed and when the data was last successfully updated.
```

---

### T2.2 — Download Signed Document Endpoint
🔴 Must-have | **Dependencies:** T2.1

**Description:** Build `GET /api/download/:id` — proxies the signed PDF from Setu through the backend, never exposing a direct Setu URL to the frontend.

**Acceptance criteria:**
- [ ] Route requires authentication and ownership verification, same pattern as T2.1
- [ ] Returns a 409/400 with a clear message if the document's status isn't `signed` yet
- [ ] Streams the file to the response by fetching Setu's returned `downloadUrl` server-side (Setu's own download endpoint returns a pre-signed link, not binary content directly — our backend fetches that link itself and passes the content through) — no intermediate temp file left behind, and the raw `downloadUrl` is never sent to the frontend
- [ ] Committed and pushed

**AI Prompt:**
```
Build a GET /api/download/:id endpoint, protected by Clerk auth and ownership verification identical to T2.1. If the document's signature_requests.status isn't "signed", return a 400 with a message like "This document hasn't been signed yet." Otherwise call setu_client.download_document, which hits Setu's GET /api/signature/:id/download/ endpoint and gets back a { downloadUrl, validUpto } pre-signed link — have your function fetch that downloadUrl server-side and stream the resulting binary content back to the client as the response. Do not write it to a temp file on disk first, and never return the raw Setu downloadUrl to the frontend — the frontend only ever sees our own /api/download/:id URL.
```

---

### T2.3 — Status Page (Frontend)
🔴 Must-have | **Dependencies:** T2.1, T4.1, T4.2

**Description:** Build the Status page — a document/request lookup or list, showing current status with manual refresh, and a download button once signed.

**Acceptance criteria:**
- [ ] Shows a list of the logged-in owner's past requests as cards, matching the Card + status-badge spec from Frontend_Specification_SignFlow.md
- [ ] Each card shows filename, signer mobile number, status badge, and a relative timestamp ("as of 3 minutes ago") per the "no false real-time confidence" rule in Security_and_Access_SignFlow.md, Section 5
- [ ] A manual "Refresh status" action calls T2.1's endpoint and updates the card in place
- [ ] Download button/link only appears (and is only clickable) once status is `Signed` — not just hidden via CSS, but genuinely not wired to any action before that (per Security_and_Access_SignFlow.md, Section 4, "Download requested before signing is complete")
- [ ] Empty state (zero documents) matches the copy guidance in Frontend_Specification_SignFlow.md, Section 8
- [ ] Committed and pushed

**AI Prompt:**
```
Build the Status page at frontend/app/status/page.tsx. Fetch and display the logged-in user's signature requests as a list of cards, styled per Frontend_Specification_SignFlow.md (status-colored left border, status badge, filename, signer mobile number, and a relative "as of X minutes ago" timestamp). Add a manual "Refresh status" action per card that calls the signature-status endpoint from T2.1 and updates that card in place. Only render the download button as clickable once a card's status is "Signed" — for any other status it should not exist as an interactive element at all, not just be visually disabled. Show an empty state with the exact copy: "No documents yet. Upload a contract to send it for signature." when the list is empty.
```

---

## Phase 3 — Error Handling & Robustness

### T3.1 — Global Error Handling Middleware
🔴 Must-have | **Dependencies:** T1.2

**Description:** Add backend-wide error handling so no raw exception, stack trace, or database error ever reaches the frontend.

**Acceptance criteria:**
- [ ] A global FastAPI exception handler catches unhandled exceptions and returns a generic `{ error: "Something went wrong. Please try again shortly." }` with a 500, logging the real error server-side only
- [ ] Specific, expected errors (validation, Setu timeout, not-found) still return their specific, human messages — this handler is a safety net, not a replacement for specific handling
- [ ] Verified by a test that triggers an unexpected exception and confirms no internal detail appears in the response body
- [ ] Committed and pushed

**AI Prompt:**
```
Add a global exception handler to the FastAPI app that catches any unhandled exception, logs the full error server-side (not to the client), and returns a generic JSON response { "error": "Something went wrong. Please try again shortly." } with a 500 status. This should not interfere with specific error responses already returned by individual endpoints (validation errors, Setu timeouts, not-found responses) — it's a catch-all safety net for anything unexpected. Add a test that deliberately triggers an unhandled exception in a route and asserts the response contains no stack trace, database error text, or internal file paths.
```

---

### T3.2 — Sandbox/Production Credential Guard
🟡 Should-have | **Dependencies:** T1.1

**Description:** A startup check that fails loudly if Setu credentials and `SETU_BASE_URL` are mismatched (sandbox creds pointed at a production URL or vice versa), per Security_and_Access_SignFlow.md, Section 5.

**Acceptance criteria:**
- [ ] On app startup, a check confirms the credential type implied by config matches `SETU_BASE_URL`'s environment
- [ ] Mismatch causes the app to fail to start with a clear log message, not a silent misconfiguration
- [ ] Committed and pushed

**AI Prompt:**
```
Add a startup check in the FastAPI app's config loading that validates SETU_BASE_URL matches the expected environment (sandbox vs production) implied by an ENVIRONMENT variable. If they're mismatched (e.g., ENVIRONMENT=production but SETU_BASE_URL still points to a sandbox domain, or vice versa), the app should fail to start and log a clear error explaining the mismatch, rather than starting up in a silently misconfigured state.
```

---

### T3.3 — Expired/Failed Link Handling (Signer-Facing)
🟡 Should-have | **Dependencies:** T2.1

**Description:** Handle the case where a signer opens an expired or already-used signing link.

**Acceptance criteria:**
- [ ] If a signer's link has expired per Setu's status response, the Status page reflects "Expired," not a stale "Pending" (per Security_and_Access_SignFlow.md, Section 4)
- [ ] Signer opening the link twice after signing sees a clear "already signed" state rather than being able to attempt signing again (this may be inherently handled by Setu's own hosted flow — verify and document the actual behavior)
- [ ] Committed and pushed

**AI Prompt:**
```
Ensure that when Setu's signature-status response indicates a request has expired, the backend updates signature_requests.status to "expired" (not left as "pending"), and the Status page frontend displays "Expired" clearly, distinct from "Pending" and "Signed". Investigate and document what happens when a signer opens their signing link a second time after already signing — confirm whether Setu's hosted flow already prevents re-signing, and if not, add a guard.
```

---

## Phase 4 — Design System Implementation

### T4.1 — Design Tokens Setup
🔴 Must-have | **Dependencies:** T0.1

**Description:** Configure Tailwind (or CSS variables) with every color, type, and spacing token from Frontend_Specification_SignFlow.md, Sections 1–4.

**Acceptance criteria:**
- [ ] All colors from Section 1 exist as named Tailwind theme colors (`paper`, `ink`, `ink-muted`, `line`, `signature`, `signature-hover`, `status-pending`, `status-signed`, `status-expired`)
- [ ] Newsreader, Public Sans, and IBM Plex Mono are loaded and mapped to `font-display`, `font-body`, `font-mono` (or equivalent)
- [ ] The type scale from Section 2 exists as reusable text style utilities/classes
- [ ] The 8px spacing scale from Section 4 is the theme's spacing scale
- [ ] Committed and pushed

**AI Prompt:**
```
Configure the Next.js frontend's Tailwind theme with this exact design system from Frontend_Specification_SignFlow.md: [paste Sections 1, 2, and 4 in full — colors, typography, spacing]. Add named theme colors for paper, ink, ink-muted, line, signature, signature-hover, status-pending, status-signed, status-expired. Load Newsreader, Public Sans, and IBM Plex Mono as font families mapped to font-display, font-body, and font-mono. Set the spacing scale to the 8px-based scale specified. Create reusable text style classes for the type scale (display-lg, display-sm, heading, body, body-sm, caption, mono).
```

---

### T4.2 — Core Component Library
🔴 Must-have | **Dependencies:** T4.1

**Description:** Build Button, Input, Card, Modal, and Badge components exactly per Frontend_Specification_SignFlow.md, Section 3, using 21st.dev components as scaffolding and re-skinning per Section 6's rule.

**Acceptance criteria:**
- [ ] Button component supports primary/secondary/destructive variants matching the exact spec table (colors, padding, radius, hover, disabled states)
- [ ] Input component matches spec including the focus ring and error state
- [ ] Card component matches spec including the status-color left-border accent
- [ ] Modal matches spec including overlay opacity, no blur, and footer button order (Cancel left, confirm right)
- [ ] Badge matches spec (pill shape, 12%-opacity background, full-strength text color)
- [ ] None of the components retain a visible 21st.dev default shadow/radius/font — spot-checked against Section 6's "re-skinning rule"
- [ ] Components are keyboard-accessible (visible focus states, modal focus trap)
- [ ] Committed and pushed

**AI Prompt:**
```
Build a component library in frontend/components/ui/ with Button, Input, Card, Modal, and Badge components. Use 21st.dev's Buttons, Cards, Dialogs, and Badges categories as structural scaffolding (focus trap on modal, accessible input labeling), but restyle every visual property to match this exact spec from Frontend_Specification_SignFlow.md, Section 3: [paste Section 3 in full]. Do not leave any default shadow, border-radius, or font from the scaffolding component — every color, spacing, and radius value must come from the design tokens set up in T4.1. Ensure all interactive elements have a visible keyboard focus state and the modal traps focus while open.
```

---

### T4.3 — Landing Page
🟡 Should-have | **Dependencies:** T4.2

**Description:** Build the landing page per Frontend_Specification_SignFlow.md's layout rules — hero section, single primary CTA into the Upload flow.

**Acceptance criteria:**
- [ ] Hero headline uses `display-lg` (Newsreader), content constrained to 960px per Section 4
- [ ] Single primary CTA button leads to the Upload page (behind login if not authenticated)
- [ ] No filler copy, no emoji, matches Section 8's copy guidance
- [ ] Committed and pushed

**AI Prompt:**
```
Build the landing page at frontend/app/page.tsx per Frontend_Specification_SignFlow.md's layout section (hero content constrained to 960px, display-lg Newsreader headline) and copy guidance in Section 8 (no filler, no emoji, plain active-voice copy). Include a single primary CTA button that routes to the Upload page — if the user isn't logged in, this should trigger the Clerk login flow first.
```

---

### T4.4 — Signature-Stroke Motion
🟢 Nice-to-have | **Dependencies:** T4.2, T2.3

**Description:** Implement the one signature GSAP animation — the pen-stroke draw on the landing hero and the "Signed" status badge checkmark — per Frontend_Specification_SignFlow.md, Section 5.

**Acceptance criteria:**
- [ ] An SVG pen-stroke draws once under the hero headline on page load, using GSAP
- [ ] The "Signed" status badge's checkmark draws in via the same technique when status transitions to Signed
- [ ] Both respect `prefers-reduced-motion`, falling back to an instant appearance
- [ ] No other GSAP animations are added beyond these two (per the spec's explicit restraint rule)
- [ ] Committed and pushed

**AI Prompt:**
```
Using GSAP, implement exactly two animations per Frontend_Specification_SignFlow.md, Section 5: (1) an SVG pen-stroke line that draws itself once under the landing page hero headline on load, and (2) a small checkmark stroke inside the "Signed" status badge that draws in when a document's status transitions to Signed. Both should respect prefers-reduced-motion by skipping the draw animation and appearing instantly instead. Do not add GSAP animations anywhere else in the app — all other micro-interactions (hovers, modal transitions) should use Motion (motion.dev), not GSAP, per the spec.
```

---

## Phase 5 — Deployment & Documentation

### T5.1 — Backend Deployment
🔴 Must-have | **Dependencies:** T3.1

**Description:** Deploy the backend to Render or Railway with production environment variables and a connected production Postgres instance.

**Acceptance criteria:**
- [ ] Backend is reachable at a public HTTPS URL
- [ ] All environment variables from Technical_Architecture_SignFlow.md, Section 4, are set in the platform's environment variable store (not committed anywhere in the repo)
- [ ] `alembic upgrade head` has been run against the production database
- [ ] CORS is configured to allow only the deployed frontend's URL, not `*` (per Security_and_Access_SignFlow.md/Technical Architecture "configuration notes")
- [ ] Committed and pushed

**AI Prompt:**
```
Prepare the backend for deployment to Render or Railway: add any required start command/Procfile, confirm environment variables are read from the platform's environment store rather than a committed .env file, and configure CORS middleware to allow only the FRONTEND_URL environment variable's origin — not a wildcard. Document the exact deployment steps (build command, start command, required env vars, migration command) in backend/README.md.
```

---

### T5.2 — Frontend Deployment
🔴 Must-have | **Dependencies:** T4.3, T5.1

**Description:** Deploy the frontend to Vercel, pointed at the deployed backend.

**Acceptance criteria:**
- [ ] Frontend is reachable at a public HTTPS URL
- [ ] `NEXT_PUBLIC_API_BASE_URL` points to the deployed backend from T5.1
- [ ] Clerk is configured with production keys, not test/dev keys
- [ ] Committed and pushed

**AI Prompt:**
```
Prepare the Next.js frontend for Vercel deployment: confirm NEXT_PUBLIC_API_BASE_URL is read from environment config and points at the deployed backend URL, confirm Clerk's production keys are used (not test keys), and document the deployment steps in frontend/README.md.
```

---

### T5.3 — Top-Level README & Documentation Finalization
🔴 Must-have | **Dependencies:** everything above

**Description:** Write the top-level `README.md` per the assignment's explicit requirements — framework choices, setup instructions, architecture overview, security considerations, database decision.

**Acceptance criteria:**
- [ ] Includes framework choices with brief reasoning (can summarize Technical_Architecture_SignFlow.md, Section 1)
- [ ] Includes setup instructions a new developer could follow from a fresh clone to a running app
- [ ] Includes an architecture overview diagram or description (Frontend → Backend → Setu)
- [ ] Includes a security considerations section summarizing Security_and_Access_SignFlow.md's key points (unguessable links, credentials server-side only, RLS approach)
- [ ] Includes the database schema decision and a link/reference to the full schema doc
- [ ] Links to all four spec docs in `docs/`
- [ ] Committed and pushed

**AI Prompt:**
```
Write the top-level README.md for this repository. Include: (1) framework choices with one-sentence reasoning for each, summarizing Technical_Architecture_SignFlow.md Section 1; (2) setup instructions taking a new developer from a fresh git clone to a running app locally, covering both backend and frontend; (3) a short architecture overview describing the Frontend → Backend → Setu request flow; (4) a security considerations section covering unguessable signing links, server-side-only credentials, and the row-level ownership model; (5) the database schema decision (Postgres, three tables, relationships) with a link to docs/Technical_Architecture_SignFlow.md for the full schema; (6) links to all four docs in the docs/ folder.
```

---

## Phase 6 — Deferred Nice-to-Haves (Post-MVP)

These match the PRD's explicit "NOT building in v1" list. Only attempt these after every 🔴 and 🟡 ticket above is complete and pushed.

### T6.1 — Real-Time Status Polling
🟢 Nice-to-have | **Dependencies:** T2.3

**AI Prompt:**
```
Replace the manual "Refresh status" button on the Status page with automatic polling every 15–30 seconds while a request is "Pending", stopping automatically once status becomes "Signed" or "Expired". Keep the manual refresh option available alongside it.
```

### T6.2 — Webhook Support
🟢 Nice-to-have | **Dependencies:** T2.1

**AI Prompt:**
```
Add a POST /api/webhooks/setu endpoint that receives status update push notifications from Setu, verifies the request using a SETU_WEBHOOK_SECRET, and updates the corresponding signature_requests row without requiring a manual status check. Fall back to the existing manual/polling status check if webhook delivery fails.
```

### T6.3 — Multi-Signer Sequencing
🟢 Nice-to-have | **Dependencies:** T1.3

**AI Prompt:**
```
Extend the signature request flow to support multiple signers with an optional signing order, using the existing signers table (already designed for this in the schema). Update the Upload page to allow adding multiple signer mobile numbers, and the Status page to show per-signer status individually.
```

### T6.4 — Embedded Signing Iframe
🟢 Nice-to-have | **Dependencies:** T2.3

**AI Prompt:**
```
Add an option on the Status page to sign within an embedded iframe pointed at the signerUrl, instead of only opening it in a new tab. Handle the case where Setu's flow doesn't support iframe embedding by falling back to the new-tab link.
```

### T6.5 — Team Accounts
🟢 Nice-to-have | **Dependencies:** T0.3, T5.3

**AI Prompt:**
```
Extend the single-Owner auth model to support inviting Team Members, per the roles defined in Security_and_Access_SignFlow.md Section 2. Add an organization_id concept, migrate owner_id usage on documents to reference an organization rather than a single user, and add an invite flow using Clerk's organization features.
```

---

## Ticket count summary

| Priority | Count |
|---|---|
| 🔴 Must-have | 15 |
| 🟡 Should-have | 3 |
| 🟢 Nice-to-have | 7 |
| **Total** | **25** |
