# WriteSpace

WriteSpace is a public-first editorial reading surface. This foundation exposes a small, safe post-preview API and a responsive React landing page.

## Run locally

### Backend

```sh
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=. .venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend reads `backend/.env`; copy `.env.example` if you need to reset local values. SQLite data is stored in the file named by `DATABASE_URL`.

### Frontend

```sh
cd frontend
npm install
npm run dev
```

The Vite proxy forwards `/api` to `VITE_DEV_API_TARGET`. Production builds use the same-origin default for `VITE_API_BASE_URL`.

## Test

```sh
cd backend
PYTHONPATH=. python -m pytest -q tests/test_public_and_health.py
cd ../frontend
npm test
```

The Playwright public-reading specification is provided in `frontend/e2e/public.spec.js` and is intended for a live backend and frontend; it is not run as part of this foundation setup.

## Containers

```sh
docker compose up --build
```

The backend data persists in the named `backend_data` volume. The development seed creates only the default `admin` user with password `admin`; it does not create public posts.
