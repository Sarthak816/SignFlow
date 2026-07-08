# SignFlow — Frontend

Next.js 15 (App Router, TypeScript) frontend for the SignFlow e-signature platform.

## Stack

- **Next.js 15** — React framework with App Router
- **TypeScript** — type safety across the UI
- **Tailwind CSS 4** — utility-first styling
- **Clerk** — passwordless magic-link authentication
- **Motion (motion.dev)** — component micro-interactions
- **GSAP** — signature pen-stroke animation

## Local Setup

### 1. Install dependencies

```bash
npm install
```

### 2. Configure environment variables

```bash
cp .env.local.example .env.local
# Fill in NEXT_PUBLIC_API_BASE_URL and NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
```

### 3. Start the development server

```bash
npm run dev
```

The app will be available at `http://localhost:3000`.

## Pages

| Route | Description |
|---|---|
| `/` | Landing page |
| `/upload` | Upload a contract and send for signature |
| `/status` | Track signature status and download signed documents |

## Deployment

See the top-level `README.md` for Vercel deployment instructions.
