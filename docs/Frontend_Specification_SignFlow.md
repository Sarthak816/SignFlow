# Frontend Specification Document: SignFlow

**Author:** Sarthak Pal
**Status:** Draft v1.0
**Companion docs:** PRD_SignFlow.md, Technical_Architecture_SignFlow.md, Security_and_Access_SignFlow.md
**Last updated:** July 8, 2026

---

## 0. Design Direction — Why This Isn't the Default AI Look

Before the tokens: a note on what "doesn't speak AI" actually means here, so every choice below can be checked against it.

The three looks every AI tool defaults to right now are: (1) warm cream background with a terracotta accent and a big serif headline, (2) near-black background with one neon accent, (3) a hairline-ruled "broadsheet" layout with zero border-radius everywhere. SignFlow avoids all three deliberately. The subject matter — contracts, signatures, official documents — already has a real visual vernacular to borrow from instead: ruled paper, ink, stamps, ledgers, the specific weight of an official form. That's where these tokens come from, not from "what looks clean in a Dribbling shot."

Concretely, this means: no gradients, no glassmorphism, no drop shadows doing the work borders should do, no pill-shaped buttons on everything, no emoji in UI copy, and no filler microcopy ("Let's get started! 🎉"). Corners are small and consistent, not zero and not rounded-everything. Color is used to mean something (status), not to decorate.

---

## 1. Color Palette

| Token | Hex | Used for |
|---|---|---|
| `paper` | `#FAFAF8` | Base background — a cool, near-white paper tone, not the cream/terracotta combo that reads as generic-AI |
| `ink` | `#1A1A1E` | Primary text, icons, borders on dark elements |
| `ink-muted` | `#5B5A57` | Secondary text — captions, timestamps, helper text |
| `line` | `#E3E1DB` | Borders, dividers, table rules — this is the "ruled paper" line, used constantly and quietly |
| `signature` | `#2D3E82` | Primary brand/action color — a muted ballpoint-ink blue, used for primary buttons, links, and the signature-stroke motif. Never bright, never neon |
| `signature-hover` | `#232F66` | Darker shade of `signature` for hover/active states |

**Semantic status colors** (used only for status badges and related indicators — never for decoration):

| Token | Hex | Meaning |
|---|---|---|
| `status-pending` | `#9A6B12` | Muted amber/gold — "waiting on a signer," like a wax seal not yet pressed |
| `status-signed` | `#2E6B4F` | Muted forest green — "complete" |
| `status-expired` | `#A13D2E` | Muted brick red — "link expired or request failed" |

**Rule:** semantic status colors appear *only* on status badges, status dots, and the thin left-border accent of a document card matching its status. They never appear on buttons, links, or decorative elements — if red starts showing up as a button color, something's gone off-brief.

---

## 2. Typography

| Role | Typeface | Why |
|---|---|---|
| **Display** (page titles, hero headline) | **Newsreader** (serif, variable weight) | A reading-serif built for long-form text, not a display-drama serif — it has the character of a printed legal document, used at restrained weights (400–500), not the ultra-bold treatment most AI-generated pages default to |
| **Body / UI** (buttons, labels, body copy, nav) | **Public Sans** | The typeface used by the U.S. federal government's design system — it carries an inherent "official form" feel that's exactly right for a signing product, and it's specifically not Inter, which is what almost every AI-generated interface reaches for by default |
| **Mono** (document IDs, timestamps, status codes) | **IBM Plex Mono** | Used sparingly, only where data needs to look like data — a `documentId`, a timestamp, a signer token fragment. Gives those values a "this is a real system value" feel distinct from prose |

**Type scale** (base 16px, 1.25 ratio):

| Token | Size | Weight | Use |
|---|---|---|---|
| `display-lg` | 40px | Newsreader 500 | Landing page hero headline only |
| `display-sm` | 28px | Newsreader 500 | Page titles (Upload, Status) |
| `heading` | 20px | Public Sans 600 | Card titles, section headers |
| `body` | 16px | Public Sans 400 | Default body text |
| `body-sm` | 14px | Public Sans 400 | Helper text, form labels |
| `caption` | 12px | Public Sans 500, uppercase, +0.04em tracking | Status badge text, table column headers |
| `mono` | 13px | IBM Plex Mono 400 | IDs, timestamps |

Line height: 1.5 for body text, 1.15 for display/heading sizes.

---

## 3. Component Styles

### Buttons

| Property | Primary | Secondary | Destructive |
|---|---|---|---|
| Background | `signature` | `paper` | `paper` |
| Text | white | `ink` | `status-expired` |
| Border | none | 1px solid `line` | 1px solid `status-expired` |
| Border-radius | 6px | 6px | 6px |
| Padding | 10px 18px | 10px 18px | 10px 18px |
| Hover | `signature-hover` background | `line` background fill | `status-expired` background, white text |
| Font | Public Sans 600, 14px | Public Sans 600, 14px | Public Sans 600, 14px |
| Disabled | 40% opacity, no hover state | 40% opacity | 40% opacity |

No gradients, no shadows on default state. A single, subtle `0 1px 2px rgba(0,0,0,0.06)` shadow appears only on the primary button's hover state — restraint is the point.

### Inputs (text fields, file upload)

| Property | Value |
|---|---|
| Background | `paper` |
| Border | 1px solid `line` (default), 1px solid `signature` (focus) |
| Border-radius | 6px |
| Padding | 10px 12px |
| Focus ring | 2px `signature` at 20% opacity, offset 2px — always visible, never removed (accessibility floor) |
| Label | `body-sm`, `ink-muted`, positioned above the field, not floating/animated |
| Error state | Border becomes `status-expired`; a `body-sm` error message appears below in `status-expired`, plain language, no icon needed |

**File upload dropzone specifically:** a bordered rectangle (1px dashed `line`, not solid — the one deliberate exception, since "dashed" is the universal signal for "drop something here") with centered `body` text ("Drag a PDF here, or click to browse") and `body-sm` `ink-muted` helper text below ("PDF only, up to 10MB"). On drag-over, border becomes solid `signature` and background tints to `signature` at 4% opacity.

### Cards (document/request cards on the Status page)

| Property | Value |
|---|---|
| Background | `paper` |
| Border | 1px solid `line` |
| Border-radius | 8px |
| Padding | 20px |
| Status accent | 3px solid left border in the matching status color (`status-pending` / `status-signed` / `status-expired`) — this is the *only* place status color touches a card |
| Shadow | none at rest; `0 2px 8px rgba(0,0,0,0.05)` on hover, signaling interactivity without decoration |
| Layout inside | filename (`heading`) top-left, status badge top-right, signer identifier (mobile number) + timestamp (`body-sm`, `ink-muted`) below, action button bottom-right |

### Status badge

Small pill: `caption` text, 4px 10px padding, border-radius 4px (deliberately smaller than buttons/cards — badges are data, not actions), background = status color at 12% opacity, text = full-strength status color.

### Modals

| Property | Value |
|---|---|
| Overlay | `ink` at 40% opacity, no blur (blur reads as glassmorphism — avoided) |
| Modal background | `paper` |
| Border-radius | 10px |
| Border | 1px solid `line` |
| Shadow | `0 8px 24px rgba(0,0,0,0.12)` — the one place a real shadow is justified, since the modal needs to visually separate from the page behind it |
| Width | 480px max, 90vw on mobile |
| Header | `heading` title + a plain "×" close control top-right (Public Sans, not an icon font) |
| Footer | Secondary button (Cancel) left, Primary button (confirm action) right — always in that order, always that alignment, everywhere in the app |

Used only for genuinely blocking decisions: confirming cancellation of a signature request, confirming a destructive action. Never used for content that could just be an inline state (status updates, success messages).

---

## 4. Spacing & Layout Rules

**Base unit: 8px.** Every margin, padding, and gap is a multiple of 8 (with 4px allowed as a half-step for tight cases like badge padding).

| Token | Value |
|---|---|
| `space-xs` | 4px |
| `space-sm` | 8px |
| `space-md` | 16px |
| `space-lg` | 24px |
| `space-xl` | 40px |
| `space-2xl` | 64px |

**Layout:**
- Max content width: **720px** for the Upload and Status pages (this is a document-focused tool, not a dashboard — content should read like a form, not sprawl edge to edge)
- Landing page hero section: full-width background, content constrained to 960px
- Page horizontal padding: `space-lg` (24px) on mobile, `space-xl` (40px) on desktop
- Vertical rhythm between major sections: `space-2xl` (64px)
- Card grids (Status page document list): single column on mobile, single column on desktop too — this app is about clarity per-document, not density. Resist the urge to grid these into a dashboard.

**Breakpoints:**

| Name | Width |
|---|---|
| `mobile` | < 640px |
| `tablet` | 640–1024px |
| `desktop` | > 1024px |

---

## 5. Motion & Animation

Three libraries are in scope, each for a different job — they are not interchangeable, and using all three everywhere is exactly the kind of scattered-effects problem that makes a UI feel AI-generated.

| Library | Use it for | Don't use it for |
|---|---|---|
| **Motion (motion.dev)** | Component-level micro-interactions in React: button hover/press states, card hover lift, modal enter/exit, page-transition fades. It's the React-native choice, so it belongs in `components/` | Complex multi-step timelines — it's not built for that, and reaching for it there fights the tool |
| **GSAP** | The one signature animation: an SVG pen-stroke that draws itself, used in exactly two places — the hero landing page (drawing under the headline, once, on load) and the "Signed" status badge (a small checkmark stroke draws in when status flips to Signed). GSAP's timeline and path-drawing control is genuinely the right tool for this specific effect | Routine hover states — overkill, adds a second animation dependency for no reason if Motion already covers it |
| **anime.js** | Not used in v1. Listed here only to explicitly rule it out: Motion and GSAP together already cover every animation need in this spec, and adding a third library for redundant capability is unjustified dependency weight | — |

**The signature element:** the pen-stroke draw is SignFlow's one memorable motion moment — literally a drawn signature, tying the brand name to the interaction. It appears once per relevant view, not on every scroll or every card. Everything else in the interface should feel calm: a 150ms ease-out on hovers, a 200ms fade on modal open, and nothing else moving unprompted.

**Accessibility:** every animation respects `prefers-reduced-motion` — the pen-stroke draw becomes an instant fade-in, hover lifts are disabled, and no animation is ever the only way information is conveyed (status is always also communicated by color + text, never by motion alone).

---

## 6. Component Sourcing from 21st.dev

21st.dev is a community library of React/Tailwind components, browsable by category, installable via its CLI/MCP. Use it as a **starting structure**, not a finished look — every component pulled from there gets re-skinned to the tokens in Sections 1–4 before it ships. Relevant categories for this build:

| 21st.dev category | Used for |
|---|---|
| **File Uploads** | Base structure for the contract upload dropzone — swap in `line`/`signature` tokens and Public Sans |
| **Buttons** | Base interaction states (hover, focus, disabled handling) — replace colors, remove any gradient/shadow defaults |
| **Cards** | Base structure for the document/status card — strip default shadows, add the status-color left border described above |
| **Dialogs / Modals** | Base modal scaffold (focus trap, overlay, escape-to-close) — restyle per Section 3 |
| **Badges** | Base pill structure for the status badge |
| **Empty States** | For the Status page with zero documents — reword per the copy guidance below, don't use the component's default illustration/copy as-is |
| **Toasts** | For non-blocking confirmations ("Link copied," "Download started") |

**The re-skinning rule:** if a component still looks recognizably like its 21st.dev default after integration — same shadow depth, same default font, same rounded-full buttons — it hasn't been re-skinned enough. The tokens in this document are the source of truth; 21st.dev components are scaffolding underneath them, not the finished design.

---

## 7. Full Third-Party Integration Spec

Two services have real integration surfaces in v1. (GSAP/Motion/21st.dev are build-time tooling and libraries, not runtime services SignFlow calls — they don't belong in this section.)

### 7.1 Setu — Document & E-Signature APIs

**What it does:** Setu provides Aadhaar OTP-based eSign — the document hosting and the actual signing flow. SignFlow's backend is the only thing that ever talks to Setu directly (see Technical Architecture Doc, Section 1 — this is a hard security boundary, not a preference).

**Base URLs:** Sandbox `https://dg-sandbox.setu.co`, Production `https://dg.setu.co` — set via `SETU_BASE_URL`.

**⚠️ Signer identity correction:** Setu identifies a signer by an **Aadhaar-linked mobile number** (`identifier`), not an email address — the signer authenticates via Aadhaar OTP sent to that number. Every earlier doc's "signer email" language should now be read as "signer's mobile number." This changes the Upload page's signer input (a phone field, not an email field) and the `signers` table's primary identity field. `displayName` and `birthYear` are optional but recommended — if set, Setu validates them against the Aadhaar OTP verification and blocks signing on a mismatch.

| Call | Endpoint | Data sent | Actual response |
|---|---|---|---|
| **Upload document** | `POST /api/documents` | `multipart/form-data`: a `payload` field containing `{ "name": "..." }` and a `files` field containing the PDF (part name `document`) | `{ "id": "...", "name": "..." }` — note the field is `id`, not `documentId`; this is what gets stored as `documents.setu_document_id` |
| **Create signature request** | `POST /api/signature` | `{ documentId, redirectUrl, signers: [{ identifier, displayName?, birthYear?, signerNo, signature: { onPages, position, height, width } }] }` — up to 25 signers can be listed, though the signing UI itself supports up to 6 active at once | `{ documentId, id, redirectUrl, signers: [{ id, identifier, displayName, status, url, signatureDetails }], status }` — the top-level `id` is the `signatureId` → `signature_requests.setu_signature_id`; **each signer has their own `url`** (not one shared link) → stored per-row in `signers.signer_url`; `status` starts as `sign_initiated` |
| **Check signature status** | `GET /api/signature/:id` | `id` = our stored `setu_signature_id` in the URL path | `{ documentId, id, status, signers: [{ id, identifier, status, signatureDetails? }] }` — request-level `status` is one of `sign_initiated \| sign_pending \| sign_in_progress \| sign_complete`; per-signer `status` is one of `pending \| in_progress \| signed`. Map `sign_complete` → our internal `signed`, and treat `sign_in_progress` as informational (another signer's link is actively open — no new signer can sign until it clears or the 15-minute session expires) |
| **Download signed document** | `GET /api/signature/:id/download/` | `id` = our stored `setu_signature_id` (**not** the document id — a correction from the earlier draft) | `{ downloadUrl, id, validUpto }` — a **pre-signed, time-limited URL**, not a binary stream. Our backend must itself fetch `downloadUrl` and stream *that* content back to the browser — this preserves the "frontend never talks to Setu" rule even though Setu's own response is a redirect-style link |
| **Delete signature request** *(optional, not in original MVP scope)* | `POST /api/signature/:id/delete/` | `id` in the URL path | `204 No Content` — deletes the signature request **and its associated document**. Useful for a "cancel request" action mentioned in the Security doc's edge cases, if you choose to build it |

**Auth on every call:** `x-client-id`, `x-client-secret`, `x-product-instance-id` headers, injected only inside `services/setu_client.py` on the backend — see Security and Access Doc, Section 1, for why this never touches the frontend.

### 7.2 Auth Provider — Clerk (recommended)

**What it does:** handles passwordless email magic-link login for internal users (Owner/Team Member roles) — see Security and Access Doc, Section 1, for why passwordless was chosen over a self-built password system.

| Call | How it's made | Data involved | Expected result |
|---|---|---|---|
| **Send magic link** | Clerk's hosted `<SignIn />` component/SDK call, not a raw REST call we write ourselves | User's email address | Clerk emails a login link; no password ever exists in our system |
| **Session verification** | Clerk SDK middleware on the backend, checking the session token attached to each request | Session token (from Clerk's cookie/JWT) | A verified `userId` + `organizationId`, used to enforce the row-level security rules in the Security and Access Doc, Section 3 |

**Integration note:** Clerk is used through its official SDK, not hand-rolled HTTP calls — this is one of the few places in the app where "write less code" is the correct security decision, not a shortcut.

---

## 8. Copy Guidance (so the UI doesn't *read* AI-generated either)

- No exclamation points, no emoji, no "Let's get started!" energy anywhere in the interface
- A button's label states exactly what happens: "Send for signature," not "Submit." A toast confirms in the same words: "Sent for signature," not "Success!"
- Empty states explain what to do next in one plain sentence: "No documents yet. Upload a contract to send it for signature." — not a cute illustration with vague copy
- Errors state what happened and what to do, without apologizing or joking: "This file is over 10MB. Choose a smaller PDF." not "Oops! Something went sideways 😅"
- Status labels are exactly: **Pending**, **Signed**, **Expired** — consistent everywhere, never rephrased as "In progress" in one place and "Waiting" in another
