# SignFlow — Backend

FastAPI backend for the SignFlow e-signature platform. All Setu API communication happens here — the frontend never talks to Setu directly.

## Stack

- **FastAPI** — async Python web framework
- **SQLAlchemy + Alembic** — ORM and schema migrations
- **PostgreSQL** — relational database
- **Clerk** — session verification for authenticated routes
- **httpx** — async HTTP client for Setu API calls

## Local Setup

### 1. Create and activate a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
# Fill in SETU_CLIENT_ID, SETU_CLIENT_SECRET, SETU_PRODUCT_INSTANCE_ID,
# DATABASE_URL, CLERK_SECRET_KEY, and FRONTEND_URL in .env
```

### 4. Run database migrations

```bash
alembic upgrade head
```

### 5. Start the development server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

## Environment Variables

See `.env.example` for the full list with descriptions.

## Deployment

See the top-level `README.md` for deployment instructions (Render/Railway).
