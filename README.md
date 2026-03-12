# NewsPulse MVP

NewsPulse is a React + FastAPI MVP for a personalized news aggregation product. This version focuses on the core PRD scope:

- aggregated article feed
- topic categorization
- personalized ranking by user interests
- article summaries
- bookmarking
- search

## Project Structure

```text
backend/
  app/
    database.py
    main.py
    models.py
    schemas.py
    seed.py
    services.py
  requirements.txt
  schema.sql
frontend/
  src/
    api.js
    App.jsx
    main.jsx
    styles.css
  index.html
  package.json
  vite.config.js
```

## Backend Setup

1. Create a virtual environment:

```bash
cd backend
python -m venv .venv
```

2. Activate it:

```bash
.venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Start the API:

```bash
uvicorn app.main:app --reload
```

The API runs on `http://127.0.0.1:8000`.

## Frontend Setup

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Start the frontend:

```bash
npm run dev
```

The app runs on `http://localhost:5173`.

## Production Deployment

This repo now includes production containerization for:

- `frontend`: React app built with Vite and served by Nginx
- `backend`: FastAPI app served by Uvicorn
- `db`: PostgreSQL

### Production Prerequisites

- Docker
- Docker Compose

### Run Production Stack

From the project root:

```bash
docker compose up --build -d
```

Then open:

- Frontend: `http://localhost`
- Backend health: `http://localhost/health`
- Backend direct port: `http://localhost:8000/health`

### Production Environment

Use [.env.example](C:/Users/SANJU/Desktop/Codex%20Learning/.env.example) as the starting point for deployment settings.

Important variables:

- `DATABASE_URL`: PostgreSQL connection string
- `ALLOWED_ORIGINS`: comma-separated frontend origins for CORS
- `SEED_DATA`: set to `false` in a real production environment after initial demo setup
- `VITE_API_BASE_URL`: API base URL for frontend builds

### Production Files

- [docker-compose.yml](C:/Users/SANJU/Desktop/Codex%20Learning/docker-compose.yml)
- [backend/Dockerfile](C:/Users/SANJU/Desktop/Codex%20Learning/backend/Dockerfile)
- [frontend/Dockerfile](C:/Users/SANJU/Desktop/Codex%20Learning/frontend/Dockerfile)
- [frontend/nginx.conf](C:/Users/SANJU/Desktop/Codex%20Learning/frontend/nginx.conf)

## Hosted Deployment Path

This repo is now prepared for:

- Vercel for the frontend
- Render for the FastAPI backend and PostgreSQL

### Render

Use [render.yaml](C:/Users/SANJU/Desktop/Codex%20Learning/render.yaml).

This provisions:

- a PostgreSQL database named `newspulse-db`
- a Python web service named `newspulse-api`

After creating the Render Blueprint:

1. Set `ALLOWED_ORIGINS` to your Vercel frontend domain
2. Note the deployed backend URL, for example `https://newspulse-api.onrender.com`
3. Keep `SEED_DATA=true` for first boot, then change it to `false` after initial data setup if desired

### Vercel

Point the Vercel project root to [frontend](C:/Users/SANJU/Desktop/Codex%20Learning/frontend).

Then update [frontend/vercel.json](C:/Users/SANJU/Desktop/Codex%20Learning/frontend/vercel.json):

- replace `https://replace-with-render-backend-url` with your real Render backend URL

Once that is updated, Vercel will:

- build the Vite frontend
- serve the static site
- proxy `/api/*` and `/health` to the Render backend

## Sample API Endpoints

- `GET /health`
- `GET /api/news?user_id=1`
- `GET /api/news?user_id=1&category=Technology`
- `GET /api/categories`
- `GET /api/search?q=OpenAI&user_id=1`
- `GET /api/bookmarks?user_id=1`
- `POST /api/bookmarks`
- `DELETE /api/bookmarks/{article_id}?user_id=1`
- `GET /api/users/1`
- `PUT /api/users/1/preferences`

## Database Notes

- The running MVP uses SQLite for zero-config local setup.
- The sample production schema in `backend/schema.sql` is written for PostgreSQL.
- On startup, the backend creates tables and seeds demo categories, sources, articles, and a demo user.

## MVP Design Choices

- News ingestion is represented with seeded normalized article records rather than live external fetchers.
- Deduplication is implemented with a `dedupe_key` and feed-level grouping.
- Personalization boosts articles that match the user's followed categories.
- Summaries are stored per article to mimic the summarized reading experience from the PRD.

## Remaining Work Before Real Production

- replace seeded/demo content with live ingestion jobs
- add authentication and protected bookmark endpoints
- add migrations instead of startup table creation
- add structured logging, monitoring, and error reporting
- move secrets to a secure secret manager
- add HTTPS and a real domain at the reverse proxy or load balancer layer

## Demo User

- Email: `demo@newspulse.app`
- User ID: `1`

Use this account in the MVP UI and API requests.
