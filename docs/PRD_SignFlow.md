# Product Requirements Document: SignFlow
### A Setu-Powered Contract Upload & E-Signature Platform

**Author:** Sarthak Pal
**Status:** Draft v1.0
**Last updated:** July 8, 2026

---

## 1. Overview

SignFlow is a web application that lets a business upload a contract, send it out for e-signature, and track that signature through to a signed, downloadable document — all through a clean, self-serve interface. The signing itself is powered by Setu's Aadhaar eSign APIs; SignFlow's job is to wrap that raw API capability in a product experience that a non-technical operations person can use without ever touching Postman, a JSON payload, or a support ticket.

In one sentence: **SignFlow turns "get this contract signed" from a multi-tool, multi-day chore into a three-click, real-time-tracked workflow.**

---

## 2. Problem Statement

Small and mid-sized Indian businesses — recruiting agencies, freelance platforms, small NBFCs, co-working spaces, vendor-heavy operations teams — routinely need documents signed: offer letters, vendor agreements, NDAs, rental agreements. Today this happens through some combination of:

- Emailing a PDF and asking someone to "print, sign, scan, and send back"
- Using a full DocuSign/Adobe Sign subscription that's overkill (and overpriced) for teams sending fewer than 50 documents a month
- Manually chasing signers over WhatsApp to check status

The result: signature turnaround takes days instead of minutes, there's no single source of truth for "who has signed what," and small teams either overpay for enterprise e-sign tools or don't use one at all.

**The core problem SignFlow solves:** give a small operations team a lightweight, purpose-built way to send a document out for legally valid e-signature and know its exact status at any moment — without enterprise pricing or enterprise complexity.

---

## 3. Who It's For

**Primary persona — "Ops Owner" (Priya, 27, Operations Lead at a 40-person recruiting startup)**
Sends 15–30 offer letters and vendor NDAs a month. Not technical. Currently uses email + manual follow-up. Wants to upload a PDF, add a signer's email, and get notified when it's done. Price-sensitive; would never pay for a full DocuSign seat for this volume.

**Secondary persona — "Founder/Admin" (Rohan, 31, runs a small co-working space chain)**
Sends member agreements. Wants a simple dashboard showing which of this month's agreements are signed vs pending, without hiring anyone to manage it.

**Tertiary persona — "Developer/Integrator"**
A technical user at a slightly larger company who wants to call SignFlow's own backend routes (or Setu directly through us) as part of their internal tooling. Lower priority for v1, but shapes the API design.

---

## 4. Core Features

### Must-Have (v1 / MVP)

| Feature | Description |
|---|---|
| **Contract upload** | Upload a PDF (type + size validated client-side and server-side) |
| **Server-side Setu integration** | All Setu API calls (`documents`, `signature`, `signature status`, `download`) happen only through our backend; credentials never touch the frontend |
| **Signature request creation** | Attach one or more signers (by Aadhaar-linked mobile number) to an uploaded document and generate a signing link for each |
| **Signature status tracking** | A status page/dashboard showing pending / signed / expired for each document |
| **Signed document download** | Once signing is complete, download the final signed PDF through the backend |
| **Persisted request metadata** | Store `documentId`, `signatureId`, `signerUrl`, `status`, and timestamps in a database rather than memory, so history survives a refresh or restart |
| **Basic error/empty states** | Clear feedback for failed uploads, invalid files, expired links, and "no documents yet" |

### Nice-to-Have (v1.x, post-MVP)

| Feature | Description |
|---|---|
| **Real-time status polling** | Auto-refresh status instead of requiring a manual re-check |
| **Webhook-based status updates** | Setu pushes status changes to us instead of us polling |
| **Multi-signer sequencing** | Support ordered signing (Signer A must sign before Signer B is notified) |
| **Embedded signing iframe** | Sign inside SignFlow itself instead of opening a new tab |
| **Responsive/mobile polish** | Fully usable on a phone, not just desktop |
| **Notifications** | Email/SMS alert to the sender when a document is signed |
| **Templates** | Reusable contract templates instead of uploading a fresh PDF each time |
| **Team accounts / multi-user** | More than one login per organization with shared visibility into documents |

---

## 5. User Flow (Start to Finish)

1. **Land on the app** → Priya opens SignFlow and sees a simple landing page with a single primary action: "Send a document for signature."
2. **Upload** → She uploads a PDF offer letter. The app validates it's a PDF under the size limit and shows an upload progress indicator.
3. **Add signer** → She enters the candidate's Aadhaar-linked mobile number as the signer.
4. **Request created** → The backend uploads the document to Setu, creates a signature request, and returns a `documentId`, `signatureId`, and `signatureUrl`. Priya sees a confirmation screen with the status ("Pending") and a shareable signing link.
5. **Signer signs** → The candidate opens the link (new tab) and completes Aadhaar eSign through Setu's flow.
6. **Status check** → Priya returns to SignFlow's Status page any time, enters or selects the request, and sees the live status pulled fresh from Setu ("Pending" → "Signed").
7. **Download** → Once signed, a "Download signed document" button appears. Clicking it fetches the final PDF through SignFlow's backend (never directly from Setu).
8. **History** → All past requests remain visible on a dashboard, each with its current status, so Priya never has to remember which document she sent when.

---

## 6. What the MVP Looks Like

The MVP is the smallest version of SignFlow that lets one person send one document, get it signed, and download it — with a persistent record of what happened. Concretely:

- **Three screens:** Landing → Upload → Status/Download
- **One signer per document** (no sequencing, no multi-party logic)
- **One backend, one database table** (documents/signatures with status + timestamps)
- **Manual status refresh** (a button, not real-time polling — polling is a v1.x upgrade)
- **New-tab signing** (not embedded — embedding is a v1.x upgrade)
- **No teams, no templates, no notifications**

If it does exactly this — reliably, with correct error handling and no credentials ever exposed to the frontend — it's a shippable MVP.

---

## 7. Success Metrics

Since this starts as a small, single-team tool rather than a funded product with a large user base, success in v1 is about **reliability and time saved**, not growth metrics:

- **Time-to-signed:** median time between "document uploaded" and "signed document downloaded" — the number this product exists to shrink
- **Completion rate:** % of signature requests that reach "Signed" status (vs abandoned/expired) — indicates whether the flow is actually usable for the signer, not just the sender
- **Status-check reliability:** % of status checks that return the correct, current state from Setu with no errors
- **Zero credential leaks:** no Setu credentials ever appear in frontend network requests, logs, or client bundles — a hard security bar, not a soft metric
- **Manual-follow-up reduction (qualitative):** for the primary persona, whether she reports no longer needing to chase signers over WhatsApp/email for status

---

## 8. Deliberately NOT Building in v1

- **Multi-signer / sequential signing** — one signer per document only
- **Real-time push updates via webhooks** — status is checked on demand, not pushed
- **Embedded in-app signing** — signer completes the flow on Setu's own hosted page
- **Templates or reusable document library** — every send starts from a fresh upload
- **Team accounts, roles, or permissions** — single-user access in v1
- **Notifications (email/SMS)** — no automated alerts when status changes
- **Mobile-optimized UI** — desktop-first; mobile responsiveness is explicitly deferred
- **Support for non-PDF file types** — PDF only
- **Any signature provider other than Setu** — no DocuSign/Adobe Sign fallback or multi-provider abstraction

These are excluded not because they're low-value, but because each one adds real complexity (sequencing logic, webhook infra, permission models) that isn't needed to prove the core loop works: upload → sign → track → download.

---

## 9. Notes on Technical Approach (for engineering handoff)

- Frontend never talks to Setu directly — all calls route through the backend, matching the architecture: `Frontend → Backend → Setu APIs`
- Backend exposes: `POST /api/upload-contract`, `GET /api/signature-status/:id`, `GET /api/download/:id`
- Secrets (`x-client-id`, `x-client-secret`, `x-product-instance-id`) live only in backend `.env`, with a documented plan for how they'd move to a proper secrets manager in production
- Database (Postgres recommended) persists request metadata rather than holding it in memory, so state survives restarts
