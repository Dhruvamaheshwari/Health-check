# Predictive Healthcare Triage & Readmission Risk Visualizer

Vue 3 + D3 dashboard over a FastAPI + scikit-learn service. One Docker image serves both.
All data is synthetic; this is a demo, not a clinical tool.

## Layout
```
backend/    FastAPI app (main.py), tests/, requirements*.txt
frontend/   Vue 3 + Vite + D3
Dockerfile  multi-stage: builds the UI, then serves UI + API from one container
render.yaml one-click Render blueprint
.github/    CI: tests, frontend build, docker build
```

## Run locally (dev)
```bash
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn main:app --reload --port 8000          # API, docs at /docs
pytest -q                                      # tests

cd frontend && npm install && npm run dev      # http://localhost:5173 (proxies /api to :8000)
```

## Run with Docker
```bash
docker compose up --build                      # http://localhost:8000
```

## Deploy
The image listens on `$PORT` (default 8000), exposes `/api/health`, and needs no database.

- **Render:** push to GitHub, then New > Blueprint, and pick the repo. `render.yaml` does the rest.
- **Railway / Fly.io / Google Cloud Run / Azure Container Apps:** deploy the `Dockerfile` as a web service. Set the health check to `/api/health`.
  Fly: `fly launch` then `fly deploy`. Cloud Run: `gcloud run deploy --source .`.
- **Any VPS:** `docker compose up -d --build`, then put Caddy or nginx in front for HTTPS.

Give the container at least 512 MB of RAM. The model trains at startup (a few seconds), so allow about 40 s for the first health check.

## Configuration
| Variable | Default | Purpose |
|---|---|---|
| `PORT` | 8000 | Listen port |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated origins. Only needed if the UI is hosted on a different origin than the API. |
| `STATIC_DIR` | `backend/static` | Where the built UI is served from |

## API
`GET /api/health`, `GET /api/meta`, `GET /api/cohort`, `POST /api/predict` with `{"features": {...seven factors...}}`.

## Going beyond the demo
- Replace `synth()` in `backend/main.py` with your own feature loading, and keep the `KEYS` contract.
- Train offline, save the model with `joblib`, and load it at startup instead of training on boot.
- Before any clinical use: validate calibration and fairness, add authentication, audit logging and PHI controls, and get clinical and regulatory review.
