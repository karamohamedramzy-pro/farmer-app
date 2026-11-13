# TB-farm React + FastAPI BETA

React and the PWA are connected to the existing in-memory FastAPI BETA through same-origin JSON endpoints in `app/web.py`. This is **not production-ready**: the existing demo account and data are in server memory, all changes are lost when the server restarts, WhatsApp delivery and real storage are not implemented, and demo codes are enabled by default. Do not use real credentials or personal data.

## Unified local run

From the repository root:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd frontend
npm ci
npm run build
cd ..
uvicorn app.web:app --host 127.0.0.1 --port 8000 --workers 1
```

Open `http://127.0.0.1:8000`. On Windows use `venv\Scripts\activate` instead. Build again after frontend changes. The server serves both the built SPA and `/api` at the same origin. The Dockerfile builds and serves the same app; `docker compose up --build` is for local BETA only.

The existing demo email is `demo@example.com`. The server generates a signed link and a random code; with `DEV_SHOW_CODES=1` they appear in the browser. No real WhatsApp is delivered. The built-in sample data remains the server's existing BETA data; no new startup seeding was added. Records persist across page refresh while the server process remains alive, but not across server restarts. Use one worker; multiple workers would have divergent in-memory state. Subscription codes belong to one demo user until restart.

## Frontend development

Run the backend on port 8001:

```bash
uvicorn app.web:app --host 127.0.0.1 --port 8001 --workers 1
```

In another terminal run:

```bash
cd frontend
npm ci
npm run dev
```

Open the Vite URL. Vite proxies `/api` server-side to `127.0.0.1:8001`; browser code only uses relative URLs. `API_TARGET` overrides the proxy target if needed. Run `npm test` for frontend tests; from the root install `requirements-dev.txt` and run `pytest` for backend tests. The standalone old template application is still available as `app.main:app` but is not the React server.

## PWA

The login controls install the same web app on the current device, not an APK, app-store package or desktop executable. Installation depends on browser support and requires HTTPS or localhost. On iPhone/iPad use Safari → Share → Add to Home Screen. Open an embedded preview in a separate tab for installation. `npm run build` creates the versioned service worker; it is not registered by Vite development mode.

The worker caches public static assets only; API responses, sessions and writes are never cached. The shell can load offline after an online visit, but login and data operations require the server; there is no offline persistence or sync. Updates wait for existing controlled pages to close. Deploy the complete build at the origin root, with `/api` routed to the same server, real files for the manifest and service worker, and SPA fallback for client routes.

## Security and deployment

Do not use this BETA for production. `DEV_SHOW_CODES=1` reveals login links and codes; the WhatsApp sender is a stub and SMTP is not configured by default. Without `SECRET_KEY`, the unified app generates a fresh random signing key per server process, so sessions and links are invalidated on restart. For a future secured deployment configure a strong persistent `SECRET_KEY`, HTTPS (`HTTPS_ONLY=1`), and a trusted public `BASE_URL`; implement real delivery, rate limiting, a durable database, backups, storage integration, authorization and a security review. Local/cloud settings are only held in server memory, may contain secrets, and are not encrypted or used to connect to storage. API state-changing requests require a session-bound CSRF token; API responses are `no-store`. The old template routes have separate security limitations documented in `doc.md`.
