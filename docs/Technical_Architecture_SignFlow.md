# Technical Architecture Document: SignFlow

**Author:** Sarthak Pal
**Status:** Draft v1.0
**Companion doc:** PRD_SignFlow.md
**Last updated:** July 8, 2026

---

## 1. Recommended Tech Stack

| Layer | Choice | Reasoning |
|---|---|---|
| **Backend framework** | **FastAPI (Python)** | Async-native, so it handles calls out to Setu (upload, create signature, poll status) without blocking. Built-in request/response validation via Pydantic means malformed uploads or signer payloads get rejected before they ever reach Setu. Auto-generated OpenAPI docs give you a free, always-current API reference to hand to a reviewer. It's also the stack your backend experience is strongest in, so decisions here come from real understanding, not a tutorial you followed once. |
| **Frontend framework** | **Next.js (React, TypeScript)** | Gives you file-based routing for the three MVP screens (Landing, Upload, Status) with minimal boilerplate. TypeScript catches shape mismatches between what the backend returns and what the UI expects — important when you're juggling `documentId`, `signatureId`, and `status` across screens. Deploys trivially to Vercel with zero server config. |
| **Database** | **PostgreSQL** | Relational data (documents → signature requests → signers) with real foreign-key relationships; you want referential integrity here, not a document store. Postgres is also explicitly named in the assignment's bonus suggestion, is free-tier available on Railway/Render/Supabase, and is a stack most interviewers will recognize instantly. |
| **ORM / migrations** | **SQLAlchemy + Alembic** | SQLAlchemy pairs naturally with FastAPI. Alembic gives you versioned schema migrations, so your README can say "run `alembic upgrade head`" instead of "manually create these tables," which reads as more production-minded. |
| **File storage (uploaded PDFs)** | **Local disk for MVP, swappable to S3-compatible storage later** | You don't need object storage complexity for a single-signer MVP handling PDFs under a few MB. Keep the storage layer behind a small interface (`storage.py`) so swapping to S3/Supabase Storage later is a one-file change, not a rewrite. |
| **Background status checks** | **None in MVP — status is fetched on demand** | Matches the MVP scope decision in the PRD (manual refresh, not polling/webhooks). Avoids needing a task queue (Celery/Redis) for v1. |
| **Auth** | **Clerk (single Owner account, passwordless magic-link login) in MVP; team roles deferred** | Reconciled with the Security and Access Doc: MVP needs exactly one logged-in identity so documents can be scoped to *someone*, and the row-level security rules have something to check against. Multi-user/Team Member roles stay deferred per the PRD — this is one account, not an org system yet — but it's a real login from day one rather than "no auth," which would leave every document ownerless. |
| **Deployment — backend** | **Render or Railway** | Both support Python + Postgres out of the box, have generous free tiers, and give you a public HTTPS URL with zero DevOps work — you want your engineering time going into the Setu integration, not into learning Kubernetes. |
| **Deployment — frontend** | **Vercel** | Zero-config Next.js deploys, automatic preview URLs per commit — useful when you're iterating and want a shareable link for each stage of the assignment. |
| **Secrets management (production notes only)** | **Environment variables in MVP; a dedicated secrets manager (AWS Secrets Manager / Doppler / Render's built-in secret store) in production** | The assignment specifically asks you to document this even if you don't implement it — see Section 4. |

---

## 2. Complete File & Folder Structure

```
signflow/
├── backend/
│   ├── app/
│   │   ├── main.py                      # FastAPI app entrypoint, CORS setup, router registration
│   │   ├── config.py                    # Loads and validates env vars (pydantic Settings)
│   │   ├── database.py                  # SQLAlchemy engine/session setup
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── document.py              # Document ORM model
│   │   │   ├── signature_request.py     # SignatureRequest ORM model
│   │   │   └── signer.py                # Signer ORM model
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── document.py              # Pydantic request/response schemas for documents
│   │   │   └── signature.py             # Pydantic request/response schemas for signatures
│   │   │
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── upload.py                # POST /api/upload-contract
│   │   │   ├── signature_status.py      # GET /api/signature-status/{id}
│   │   │   └── download.py              # GET /api/download/{id}
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── setu_client.py           # All outbound HTTP calls to Setu, credentials injected here only
│   │   │   └── storage.py               # File save/retrieve abstraction (local disk now, S3-ready later)
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── validators.py            # File type/size validation helpers
│   │
│   ├── alembic/
│   │   ├── versions/                    # Auto-generated migration files
│   │   └── env.py
│   │
│   ├── tests/
│   │   ├── test_upload.py
│   │   ├── test_signature_status.py
│   │   └── test_download.py
│   │
│   ├── .env.example                     # Documented env vars, no real values
│   ├── requirements.txt
│   ├── alembic.ini
│   └── README.md
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx                     # Landing page
│   │   ├── upload/
│   │   │   └── page.tsx                 # Upload Contract page
│   │   ├── status/
│   │   │   └── page.tsx                 # Status page (enter/select a request)
│   │   └── layout.tsx
│   │
│   ├── components/
│   │   ├── UploadDropzone.tsx
│   │   ├── StatusBadge.tsx
│   │   ├── DocumentCard.tsx
│   │   └── ui/                          # Shared low-level UI primitives (button, input, etc.)
│   │
│   ├── lib/
│   │   ├── api.ts                       # Typed fetch wrapper for calling the backend
│   │   └── types.ts                     # Shared TS types matching backend Pydantic schemas
│   │
│   ├── .env.local.example
│   ├── package.json
│   └── README.md
│
├── docs/
│   ├── PRD_SignFlow.md
│   ├── Technical_Architecture_SignFlow.md
│   ├── system-architecture-diagram.png
│   └── sequence-diagram.png
│
└── README.md                            # Top-level: setup, architecture overview, security notes
```

**Why this shape:** `routers/` stays thin (HTTP concerns only), `services/` holds the actual Setu integration and file handling, and `models/`/`schemas/` are kept separate so your database representation (`models`) never leaks directly into your API contract (`schemas`) — a reviewer looking at this structure can tell you understand separation of concerns without you having to explain it out loud.

---

## 3. Database Schema

Three tables, reflecting the real-world relationship: **one document can have one signature request, and one signature request has one or more signers.**

### `documents`

| Field | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | Internal primary key |
| `setu_document_id` | VARCHAR | The `documentId` returned by Setu after upload — this is what you'll reference in later Setu API calls |
| `owner_id` | VARCHAR | The Clerk user ID of the logged-in Owner who uploaded this document — added because MVP now includes single-account auth; this is the field every query filters on, and the field that becomes `organization_id` when team accounts ship |
| `original_filename` | VARCHAR | The name of the file as uploaded, for display purposes |
| `file_path` | VARCHAR | Where the PDF is stored (local path in MVP, S3 key later) |
| `file_size_bytes` | INTEGER | Used for validation and display |
| `uploaded_at` | TIMESTAMP | When the upload happened |

**In plain English:** this table is your record of "a PDF exists in our system," independent of whether anyone has been asked to sign it yet. Keeping it separate from `signature_requests` means you could, in theory, upload a document without immediately sending it for signature — matching how the assignment's Stage 2 flow separates "upload document" from "create signature request" as two backend steps.

### `signature_requests`

| Field | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | Internal primary key |
| `document_id` | UUID (FK → documents.id) | Which document this request is for |
| `setu_signature_id` | VARCHAR | The `id` Setu returns from `POST /api/signature` — this is the value used in every later status/download call |
| `status` | VARCHAR (enum: `pending`, `signed`, `expired`, `failed`) | Our simplified internal status. Mapped from Setu's real enum on every refresh: `sign_initiated`/`sign_pending`/`sign_in_progress` → `pending`, `sign_complete` → `signed` (see Frontend_Specification_SignFlow.md, Section 7.1, for the full mapping) |
| `redirect_url` | TEXT | Where Setu redirects the signer after signing, if configured |
| `created_at` | TIMESTAMP | When the request was created |
| `updated_at` | TIMESTAMP | Last time status was refreshed |

**Correction from an earlier draft:** `signer_url` was removed from this table — Setu returns a **separate signing link per signer**, not one link per request, so that field now lives on `signers` instead (below).

**In plain English:** this is the row that represents "someone has been asked to sign this document." It's a separate table from `documents` because a single document could theoretically be re-sent for signature (a new request) without needing a whole new upload — the relationship is one-to-many from `documents` to `signature_requests`, even though MVP usage will mostly be one-to-one.

### `signers`

| Field | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | Internal primary key |
| `signature_request_id` | UUID (FK → signature_requests.id) | Which request this signer belongs to |
| `setu_signer_id` | VARCHAR | The signer's own `id`, returned inside the `signers` array from Setu — needed to match status updates back to the right signer |
| `identifier` | VARCHAR | **Correction from an earlier draft:** Setu's eSign is Aadhaar OTP-based, so a signer is identified by their **Aadhaar-linked mobile number**, not an email address. This replaces the `email` field from the original schema |
| `display_name` | VARCHAR (nullable) | Signer's name, if collected — passed to Setu as `displayName` and optionally validated against Aadhaar OTP data |
| `signer_url` | TEXT | This signer's individual signing link, returned by Setu as `url` inside their entry in the `signers` array |
| `status` | VARCHAR (enum: `pending`, `in_progress`, `signed`) | Mirrors Setu's real per-signer status enum directly — no translation needed here, unlike the request-level status |
| `signed_at` | TIMESTAMP (nullable) | Filled in once Setu confirms this signer has signed (inferred from `status` flipping to `signed`, since Setu's response doesn't include a literal timestamp field — store the time your backend observed the change) |

**In plain English:** even though MVP only supports one signer per document, this table is still separate from `signature_requests` rather than being a single column on that table. That's a deliberate, cheap-now decision: multi-signer support (a v1.x "nice-to-have" from the PRD) becomes "add more rows," not "redesign the schema and write a migration that reshapes existing data" — and it turns out to be the *correct* shape anyway, since Setu itself returns one URL and one status per signer, not one per request.

### Relationships summary

```
documents (1) ──── (1) signature_requests (1) ──── (many) signers
```

- One document has one active signature request in MVP (schema allows more, for future re-sends)
- One signature request has one signer in MVP (schema allows more, for future multi-signer support)

---

## 4. Environment Variables & Configuration Notes

### Backend (`backend/.env`)

| Variable | Purpose | Notes |
|---|---|---|
| `SETU_CLIENT_ID` | Setu's `x-client-id` | Sandbox value during development; never logged, never returned in any API response |
| `SETU_CLIENT_SECRET` | Setu's `x-client-secret` | Same handling as above — this is the one credential that would cause real damage if leaked |
| `SETU_PRODUCT_INSTANCE_ID` | Setu's `x-product-instance-id` | Identifies which Setu product instance you're calling |
| `SETU_BASE_URL` | Setu API base URL | Keep this configurable rather than hardcoded, so switching between sandbox and production is a config change, not a code change |
| `DATABASE_URL` | Postgres connection string | Format: `postgresql://user:password@host:port/dbname` |
| `FRONTEND_URL` | The deployed frontend's URL | Used to configure CORS — only this origin should be allowed to call the backend |
| `MAX_UPLOAD_SIZE_MB` | File size limit | Enforced server-side, not just in the frontend dropzone — never trust client-side validation alone |
| `ENVIRONMENT` | `development` / `production` | Lets you toggle things like verbose error messages (fine in dev, a security risk in prod) |

### Frontend (`frontend/.env.local`)

| Variable | Purpose | Notes |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Your backend's URL | This is the *only* Setu-adjacent config the frontend ever sees — no client IDs, no secrets. `NEXT_PUBLIC_` prefix means it's bundled client-side, so double-check nothing sensitive ever gets this prefix by accident |

### Configuration notes worth writing into your README

1. **Never let a Setu credential exist in any file under `frontend/`.** The moment a variable meant for the backend gets prefixed `NEXT_PUBLIC_` in Next.js, it ships to the browser. This is the single most likely accidental security mistake in this stack — worth a one-line comment in `config.py` warning future-you about it.
2. **CORS should allow exactly one origin** (`FRONTEND_URL`), not `*`. A wildcard origin on a backend that handles file uploads and signature data is a bigger opening than it looks.
3. **`.env.example` files should be committed; `.env` and `.env.local` should not.** Add both to `.gitignore` before your first commit, not after.
4. **Production secrets belong in a secrets manager, not a `.env` file on a server.** For this project's scale, Render's and Railway's built-in encrypted environment variable storage is a reasonable "production-lite" answer — worth naming explicitly in your README since the assignment asks for it, even though a full Vault/AWS Secrets Manager setup would be overkill here.
5. **Rotate the Setu sandbox credentials if this repo is ever made public with real values committed anywhere in its git history** — a `.env` committed once and later removed still exists in old commits unless the history is rewritten.
6. **Webhook signing secret (future, not MVP):** if you add Setu webhook support later, it will come with its own secret used to verify that incoming webhook calls actually came from Setu and not a forged request. Worth a placeholder line (`SETU_WEBHOOK_SECRET=`) in `.env.example` now, even unused, so the README's "how you'd extend this" section has something concrete to point to.
