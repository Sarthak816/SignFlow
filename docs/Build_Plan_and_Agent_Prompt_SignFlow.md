# Build Plan & Master Agent Prompt: SignFlow

**Author:** Sarthak Pal
**Status:** v1.0
**Reads alongside:** PRD_SignFlow.md, Technical_Architecture_SignFlow.md, Security_and_Access_SignFlow.md, Frontend_Specification_SignFlow.md, Feature_Tickets_SignFlow.md
**Last updated:** July 8, 2026

---

## 1. Confirming this is buildable for free

Every piece of this stack has a free tier sufficient for an assignment-scale project:

| Service | Free tier | Notes |
|---|---|---|
| **GitHub** | Free | Unlimited public/private repos |
| **Render or Railway** (backend) | Free tier | Spins down on inactivity on the free tier — fine for an assignment demo, mention this in your README if a reviewer hits a cold start |
| **Vercel** (frontend) | Free (Hobby) tier | Zero-config Next.js deploys |
| **Postgres** | Free via Railway/Render's free Postgres, or Neon/Supabase free tier | Any of these work with the SQLAlchemy setup in the Technical Architecture doc |
| **Clerk** | Free tier (generous MAU limit) | Covers single-owner auth with room to spare |
| **Setu** | Sandbox environment | Free for development/testing per their sandbox program |

**Nothing in this build requires a paid plan.** If a deploy step ever prompts for billing info unexpectedly, stop and re-check you're on the free/sandbox tier before continuing.

---

## 2. The feature-by-feature build & commit rule

This is the core workflow rule for however you build this — yourself, or via an AI coding agent:

**One ticket, one build, one commit, one push. Never batch multiple tickets into a single commit.**

Why this matters for this specific submission: the assignment explicitly says reviewers may look at your commit history and ask you to explain your engineering workflow. A repo with three giant commits ("initial commit," "add stuff," "fix things") tells a reviewer nothing. A repo with 25 small, sequential, clearly-labeled commits — each mapping to a ticket in Feature_Tickets_SignFlow.md — tells them exactly how you think and work.

**Commit message format** (Conventional Commits style, ticket ID included):

```
feat(T1.2): add upload-contract endpoint with Setu integration

- Validates PDF content type and size before upload
- Calls setu_client.upload_document and creates documents row
- Handles partial failure if Setu call fails after file save
```

Use `feat` for new functionality, `fix` for bug fixes discovered mid-build, `chore` for setup/config tickets (T0.1, T0.2), `docs` for README/documentation tickets.

**Sequence to follow for every single ticket, no exceptions:**
1. Open Feature_Tickets_SignFlow.md, find the next incomplete ticket in order
2. Paste its **AI Prompt** block into your coding agent (or implement it yourself)
3. Verify every item in that ticket's **Acceptance criteria** checklist before moving on
4. `git add`, commit with the format above, referencing the ticket ID
5. `git push`
6. Check the ticket off in Feature_Tickets_SignFlow.md
7. Only then move to the next ticket

Do not let an agent "helpfully" implement three tickets at once because it's faster — that defeats the entire point of this structure and is exactly the kind of unedited, unreviewed AI output the assignment explicitly warns against.

---

## 3. Master prompt for Kiro / Antigravity

Paste this as the first message / system-level instruction in your agentic coding tool session. It points the agent at all five documents and enforces the one-ticket-at-a-time discipline.

```
You are building SignFlow, a contract upload and e-signature web app powered by Setu's APIs. Before writing any code, read these five documents in the docs/ folder in full and treat them as the single source of truth for every decision — do not deviate from them without flagging the deviation explicitly:

1. docs/PRD_SignFlow.md — what the product does and who it's for
2. docs/Technical_Architecture_SignFlow.md — tech stack, folder structure, database schema, environment variables
3. docs/Security_and_Access_SignFlow.md — auth approach, roles, row-level security rules, error handling, edge cases
4. docs/Frontend_Specification_SignFlow.md — design system (colors, type, components, spacing), motion rules, third-party API integration spec
5. docs/Feature_Tickets_SignFlow.md — the complete, ordered list of build tickets with acceptance criteria

Your workflow rule, with no exceptions: work through Feature_Tickets_SignFlow.md one ticket at a time, in the exact order listed, respecting each ticket's Dependencies field. For each ticket:

1. Implement only what that ticket's Description and AI Prompt describe — do not pull in scope from later tickets, even if it seems convenient
2. Verify every item in that ticket's Acceptance Criteria checklist yourself before considering it done
3. Make exactly one git commit for that ticket, using this format:
   feat(TICKET_ID): short description
   
   - bullet point of what changed
   - bullet point of what changed
   Use "fix" instead of "feat" for bug fixes, "chore" for setup/config tickets, "docs" for documentation tickets.
4. Push that commit before starting the next ticket
5. Stop and tell me clearly which ticket you just completed and ask before proceeding to the next one

Never batch multiple tickets into a single commit, and never skip a ticket's dependencies. If you believe two tickets are trivial enough to combine, ask me first rather than deciding on your own — the commit history itself is a deliverable for this project, not just the final app.

If any instruction in the ticket list conflicts with one of the four spec documents, stop and flag the conflict to me rather than silently picking one. Begin with the first incomplete ticket in Feature_Tickets_SignFlow.md.
```

---

## 4. What "done" looks like

By the end of the 🔴 must-have tickets (15 of them), you should have:
- A public GitHub repo with 15+ commits, each mapping to one ticket
- A deployed backend (Render/Railway) and deployed frontend (Vercel), both free tier
- Every environment variable documented and none committed to the repo
- A README that satisfies every bullet point in the assignment's Stage 2 deliverables section
- A working end-to-end flow: log in → upload a PDF → send for signature → check status → download once signed

The 🟡 should-have and 🟢 nice-to-have tickets are exactly what the assignment's "Bonus" scoring category rewards — attempt them in order, after the must-haves are solid, not before.
