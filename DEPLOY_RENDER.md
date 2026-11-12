# Automated Backend Deployment to Render (Axoora Sovereign Fintech)

This document provides a complete guide to deploying and automating the Axoora Django backend on [Render](https://render.com).

---

## Architecture Overview

- **Runtime**: Python 3.12 (WSGI via Gunicorn)
- **Static Assets**: WhiteNoise (`CompressedManifestStaticFilesStorage`)
- **Database**: Render Managed PostgreSQL (via `DATABASE_URL`) with automatic SQLite fallback
- **Health Check**: `/health/`
- **Build Script**: `./build.sh`
- **Infrastructure as Code**: `render.yaml` (Render Blueprint spec)
- **CI/CD Pipeline**: `.github/workflows/deploy.yml` (Runs 34 test suites on push, then triggers Render deploy)

---

## Method 1: Render Blueprint (Recommended · One-Click)

1. Log in to [dashboard.render.com](https://dashboard.render.com).
2. Click **New +** in the top navigation and select **Blueprint**.
3. Connect your GitHub repository:
   - If using the dedicated backend repository: `Moosaa95/axoora-backend`
   - If using the monorepo: `Moosaa95/axoora-website-update`
4. Render will automatically detect `render.yaml` and provision:
   - **`axoora-backend`** (Python Web Service)
   - **`axoora-postgres`** (Managed PostgreSQL database)
   - Automatic environment variables (`SECRET_KEY`, `DATABASE_URL`, `PYTHON_VERSION`)
5. Click **Apply**.
6. Render builds the project using `./build.sh`, applies migrations, verifies the admin account, seeds data, and starts Gunicorn.

---

## Method 2: Manual Web Service Setup on Render

If you prefer setting up the web service manually:

1. Click **New +** -> **Web Service**.
2. Connect your repository: `Moosaa95/axoora-backend`.
3. Configure the following service settings:
   - **Name**: `axoora-backend`
   - **Region**: `Frankfurt (EU Central)` (lowest latency to EMEA & Nigeria) or `Oregon (US West)`
   - **Branch**: `main`
   - **Runtime**: `Python`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120`
   - **Health Check Path**: `/health/`
   - **Auto-Deploy**: `Yes`
4. In **Environment Variables**, configure:

| Key | Example Value | Description |
| --- | --- | --- |
| `PYTHON_VERSION` | `3.12.3` | Python runtime version |
| `DEBUG` | `False` | Production mode |
| `SECRET_KEY` | *(Click Generate)* | Cryptographic signing key |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,.onrender.com` | Allowed domains |
| `CORS_ALLOW_ALL` | `false` | Restrict origins |
| `CORS_ALLOWED_ORIGINS` | `https://your-frontend.vercel.app,http://localhost:3000` | Allowed frontend URLs |
| `CSRF_TRUSTED_ORIGINS` | `https://*.onrender.com,https://your-frontend.vercel.app` | CSRF origins |
| `AUTO_SEED_DATA` | `true` | Auto-seed CMS & RAG data on first boot |
| `DATABASE_URL` | *(Postgres connection string or leave blank for SQLite)* | Database URL |

---

## Automated CI/CD with GitHub Actions

The repository includes `.github/workflows/deploy.yml`:
1. Every push to `main` automatically runs Django `manage.py check` and all **34 unit tests**.
2. If all tests pass, it calls your Render Deploy Hook.

### To enable the Deploy Hook:
1. In your Render Web Service dashboard, navigate to **Settings** -> **Deploy Hook**.
2. Copy the URL (format: `https://api.render.com/deploy/srv-xxxxxx?key=yyyyyy`).
3. In your GitHub repository (`Moosaa95/axoora-backend`), go to **Settings** -> **Secrets and variables** -> **Actions**.
4. Click **New repository secret**:
   - **Name**: `RENDER_DEPLOY_HOOK_URL`
   - **Value**: *(Paste your Render Deploy Hook URL)*
5. Click **Add secret**.

Now, any time you push code to `main`:
- GitHub Actions verifies test integrity.
- Render immediately deploys the update with zero downtime.
