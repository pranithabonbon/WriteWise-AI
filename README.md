# WriteWise AI

WriteWise AI is a writing analysis platform. The Flask API checks grammar, readability, vocabulary, and sentence complexity. The React frontend talks to that API. Phase 5 adds optional AI-powered rewrites and writing feedback.

Phase 4 adds document upload. The API accepts a `.txt`, `.pdf`, or `.docx` file, extracts the text, and can run the same analysis used by `POST /api/analyze`.

## Supported file formats

| Format | Extension | What is extracted |
| --- | --- | --- |
| Plain text | `.txt` | File text, including UTF-8, UTF-8 with BOM, UTF-16, and Windows-1252 |
| PDF | `.pdf` | Text from every page |
| Word | `.docx` | Paragraphs and table cells |

The file extension is not enough on its own. The server also checks the file contents, so a renamed or corrupted file is rejected. Password-protected PDFs are rejected.

**Maximum file size: 5 MB.**

## Run the API

From `backend`, with the virtual environment active:

```powershell
.\venv\Scripts\Activate.ps1
python run.py
```

The API listens on `http://127.0.0.1:5001` unless `PORT` is set.

## Run locally with Docker Compose

Docker Compose runs the Flask API and Vite development server in separate containers. MongoDB remains on Atlas; no local database container is started. The browser opens the frontend at `http://localhost:5173`, and Vite forwards `/api` requests over the Compose network to `backend:5001`.

### Configure environment variables

Create the backend environment file from the checked-in template:

```powershell
if (!(Test-Path backend/.env)) { Copy-Item backend/.env.example backend/.env }
```

Edit `backend/.env` and add your Atlas URI and any Gemini/Anthropic credentials and model settings you need. Keep all keys and the database URI here; do not put secrets in frontend variables. Compose excludes `.env` files from image builds and injects `backend/.env` only into the backend container. The file is Git-ignored. The checked-in values are development defaults/placeholders, so AI and Atlas-backed features need valid credentials to work.

Frontend public settings are set in `docker-compose.yml` for local development. `VITE_API_BASE_URL=/api` is intentional: the browser calls its own Vite origin and Vite proxies requests to the backend service. Do not set it to `http://backend:5001`; that service name is only resolvable inside the Docker network, not by the browser.

### Build and start

From the repository root:

```powershell
docker compose up --build
```

Open <http://localhost:5173>. The backend API is also published at <http://localhost:5001>; check <http://localhost:5001/api/health> for its health response. The local backend image installs Java and NLTK data. LanguageTool downloads lazily on first grammar analysis, so that first request can take longer. The production Render image continues to cache LanguageTool during its build.

To run in the background:

```powershell
docker compose up --build -d
```

### Logs and stopping

```powershell
# Follow logs from both services
docker compose logs -f

# Follow one service
docker compose logs -f backend
docker compose logs -f frontend

# Stop containers and the Compose network
docker compose down
```

The source directories are mounted into the development containers, so frontend edits use Vite's hot reload and backend edits trigger Flask's reloader. Rebuild after changing dependencies or Docker configuration with `docker compose up --build`. Compose uses `backend/Dockerfile.dev`; `backend/Dockerfile` remains the production image used by Render.

### Troubleshooting

- **Frontend shows the API as offline:** confirm both services are up with `docker compose ps`, inspect `docker compose logs backend`, and check `http://localhost:5001/api/health`. Compose waits for the backend health check before starting Vite.
- **Requests fail from the browser:** keep `VITE_API_BASE_URL=/api`; Vite must proxy to `http://backend:5001` inside Compose. `localhost` inside the frontend container refers to that frontend container itself.
- **Atlas reports unreachable:** verify `MONGODB_URI`, Atlas database credentials, and that your current public IP is allowed by the Atlas project's network access list. The API can start without Atlas configured, but database-dependent features will not work.
- **AI endpoints report missing configuration:** set `LLM_PROVIDER`, the matching server-side API key, and `LLM_MODEL` in `backend/.env`, then recreate the backend with `docker compose up --build -d backend`.
- **Port already in use:** stop the process using 5173 or 5001, or change the host side of the corresponding Compose port mapping (the value before `:`).
- **Environment changes are not reflected:** recreate the service with `docker compose up -d --force-recreate backend` (or `frontend`).

## Upload API

`POST /api/upload`

Send `multipart/form-data` with a file field named `file`.

Analysis is optional. Add either of these when you want the extracted text scored by the existing analysis service:

- form field: `analyze=true`
- query string: `?analyze=true`

Accepted true values are `true`, `1`, `yes`, and `on`.

### Example request

```powershell
curl.exe -X POST "http://127.0.0.1:5001/api/upload" -F "file=@example.pdf"
```

With analysis:

```powershell
curl.exe -X POST "http://127.0.0.1:5001/api/upload" -F "file=@example.pdf" -F "analyze=true"
```

### Example response

```json
{
  "success": true,
  "message": "File uploaded and text extracted successfully.",
  "file": {
    "filename": "example.pdf",
    "file_type": "PDF",
    "character_count": 1000,
    "word_count": 180
  },
  "text": "Extracted document text..."
}
```

When analysis is requested, the response also includes an `analysis` object. That object is the result returned by `AnalysisService` (the same shape as `POST /api/analyze`): grammar, readability, vocabulary, sentence complexity, and score.

### Error responses

| Situation | Status |
| --- | --- |
| Missing file, empty file, missing filename, or corrupted file | 400 |
| File larger than 5 MB | 413 |
| Extension other than `.txt`, `.pdf`, or `.docx` | 415 |

Error bodies look like:

```json
{
  "success": false,
  "message": "The uploaded file is empty."
}
```

## Other API routes

- `GET /api/health` — API and database status
- `POST /api/analyze` — JSON body `{ "text": "..." }` for writing analysis
- `POST /api/improve` — JSON body `{ "text": "...", "tone": "Professional" }` for an AI rewrite and feedback

## AI writing improvement

Set the provider credentials in `backend/.env`. The provider key is read only by Flask; do not put it in a `VITE_` variable or send it from the browser.

```dotenv
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-server-side-google-ai-studio-key
LLM_MODEL=gemini-3.5-flash-lite
# Optional; used by /api/agent/analyze only after transient primary failures.
LLM_FALLBACK_MODEL=
LLM_TIMEOUT_SECONDS=30
```

`LLM_TIMEOUT_SECONDS` caps one Gemini attempt. AI Rewrite and the complete AI Agent flow share a 38-second backend deadline across retries, fallback, and nested rewrite calls. The frontend waits up to 45 seconds for the API response, leaving time for the backend to return a timeout response before Axios gives up.

Install the backend dependencies after updating the provider package:

```bash
cd backend
python -m pip install -r requirements.txt
```

For Anthropic, set `LLM_PROVIDER=anthropic`, `ANTHROPIC_API_KEY`, and an Anthropic model ID instead. For Gemini, set `LLM_PROVIDER=gemini`, `GEMINI_API_KEY`, and `LLM_MODEL=gemini-3.5-flash-lite`. Keep both API keys in `backend/.env`; never expose them to the frontend. The Gemini model ID is listed as a stable model in Google's current model documentation.

`POST /api/improve` accepts non-empty text up to 12,000 characters and an optional exact tone: `Professional`, `Academic`, `Formal`, `Casual`, or `Friendly`. If tone is omitted, it defaults to `Professional`. The response includes a meaning-preserving rewrite, grammar explanations with original and corrected text, and suggestions grouped under `Readability`, `Vocabulary`, `Sentence structure`, and `Repetition`.

The AI writing agent at `POST /api/agent/analyze` uses `LLM_MODEL` as its primary Gemini model. Optionally set `LLM_FALLBACK_MODEL` to another model ID enabled for your API key. After its retries are exhausted for temporary `429` or `503` errors, the agent tries that configured fallback. Permanent errors do not trigger fallback; leave the setting blank to disable it.

Example request:

```json
{
  "text": "The team complete the report yesterday.",
  "tone": "Professional"
}
```

Example response:

```json
{
  "success": true,
  "tone": "Professional",
  "rewrite": "The team completed the report yesterday.",
  "grammar_explanations": [
    {
      "original_text": "The team complete the report yesterday.",
      "corrected_text": "The team completed the report yesterday.",
      "explanation": "Use the past tense for an action that happened yesterday."
    }
  ],
  "suggestions": {
    "Readability": [],
    "Vocabulary": [],
    "Sentence structure": [],
    "Repetition": []
  }
}
```

The improvement endpoint does not save submitted text or AI results to MongoDB. Missing configuration returns `503`; invalid input returns `400`; timeouts return `504`; provider rate limits return `429`; and other provider or output errors return a generic `502` response without provider details.

## Tests

From `backend`:

```powershell
.\venv\Scripts\python.exe -m pytest -v
```

## Production deployment (Vercel + Render)

The frontend is a Vite static site and the API is a Flask service. The API is served by Gunicorn in production. The backend Docker image includes Java 17 and downloads the LanguageTool distribution during its build; Render's native Python runtime does not include the JVM LanguageTool needs. The image keeps one Gunicorn worker because the LanguageTool process is shared and serialized within the app process.

### 1. Deploy the Flask API to Render

Create a Render **Web Service** from this repository with:

| Setting | Value |
| --- | --- |
| Root Directory | `backend` |
| Runtime | `Docker` |
| Dockerfile Path | `./Dockerfile` |
| Docker Build Context Directory | `.` |
| Health Check Path | `/api/health` |

The Dockerfile starts Gunicorn on Render's injected `PORT`. Do not use `python run.py` as the production start command.

Set these variables in Render's service Environment page. Enter secret values in the dashboard only; never commit them or place them in a `VITE_` variable.

| Variable | Required value |
| --- | --- |
| `APP_ENV` | `production` |
| `SECRET_KEY` | At least 32 random characters; generate one with `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `FLASK_DEBUG` | `0` (do not enable debug in production) |
| `CORS_ORIGINS` | Exact HTTPS Vercel production origin, e.g. `https://your-project.vercel.app`; add each intended custom/preview origin as its own comma-separated origin |
| `MONGODB_URI` | Atlas application connection string (`mongodb+srv://...`) |
| `MONGODB_DB_NAME` | `writewise_ai` (or your chosen database name) |
| `MONGODB_TIMEOUT_MS` | `5000` |
| `LLM_PROVIDER` | `gemini` |
| `GEMINI_API_KEY` | Your server-side Google AI Studio API key |
| `LLM_MODEL` | A Gemini model ID enabled for that key |
| `LLM_FALLBACK_MODEL` | Optional Gemini model ID for agent fallback after temporary primary-model `429`/`503` errors |
| `LLM_TIMEOUT_SECONDS` | `30` maximum for each Gemini attempt; total AI request budget is 38 seconds |
| `MAX_UPLOAD_MB` | `5` |

The service refuses to start in production if the secret, exact HTTPS CORS origin, Atlas URI, or selected AI provider credentials/model are missing or invalid. CORS does not accept `*` in production.

In Atlas, create a database user with only the access this app needs and add the Render service's outbound IP ranges to the Atlas project IP access list. Find the current ranges in the Render service's **Connect → Outbound** panel; Render ranges are region-specific and may be shared. Avoid `0.0.0.0/0`. Atlas requires the client source to be allowlisted and the database user to authenticate. [Render outbound IP guidance](https://render.com/docs/outbound-ip-addresses), [Atlas connection troubleshooting](https://www.mongodb.com/docs/atlas/troubleshoot-connection/).

To verify the Atlas connection and create the app's indexes, configure a local backend environment with the same Atlas URI, allowlist your current IP in Atlas temporarily, then run `python -m scripts.setup_db` from `backend`. The script performs a temporary write/read/delete check and removes its check document.

The app connects to Atlas lazily and the health endpoint reports the database state. After creating the Render service, check `GET https://<service>.onrender.com/api/health` and confirm `database` is `connected`.

### 2. Deploy the React frontend to Vercel

Import this repository as a Vercel project and set:

| Setting | Value |
| --- | --- |
| Root Directory | `frontend` |
| Framework Preset | `Vite` |
| Node.js Version | `22.x` (Vite requires Node `20.19+` or `22.12+`; use the current 22.x runtime) |
| Build Command | `npm run build` |
| Output Directory | `dist` |

Set this Vercel environment variable for Production (and Preview too if you intend to use previews):

```dotenv
VITE_API_BASE_URL=https://<your-render-service>.onrender.com/api
```

Set `VITE_APP_NAME` and `VITE_MAX_UPLOAD_MB` only if you want to override their defaults. Vite embeds every `VITE_` value in browser assets, so use this prefix only for public settings. API keys, `SECRET_KEY`, and `MONGODB_URI` belong only in Render. The SPA rewrite in `frontend/vercel.json` supports direct loading of the History route. Vercel’s Vite docs describe the SPA rewrite and build-time environment behavior: [Vite on Vercel](https://vercel.com/docs/frameworks/frontend/vite).

After the first Vercel deploy, copy its exact HTTPS origin into Render's `CORS_ORIGINS`, save, and redeploy the API. Add custom domains there as well. Preview URLs are separate origins; add only the preview origins you explicitly want to allow.

### 3. Local development after deployment configuration

Keep the checked-in examples as templates and create local files from them:

```powershell
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

In `backend/.env`, use `APP_ENV=development`, `FLASK_DEBUG=1`, local CORS origins, and your local Atlas/Gemini values if you want those features. In `frontend/.env`, keep `VITE_API_BASE_URL=/api`; Vite proxies `/api` to `http://127.0.0.1:5001`. Run the Flask development server from `backend` and Vite from `frontend` as described above. Local grammar checking needs Java 17 or later; if a cached LanguageTool install is not present, the wrapper downloads it into its cache on first check. `WRITEWISE_LANGUAGETOOL_JAR_DIR` is optional for pointing at an existing installation.

### Upload and persistence behavior

The application accepts up to 5 MB per file. Flask allows an additional 64 KiB for multipart request framing, while `FileExtractor` enforces the exact file-byte limit. The extractor reads the request stream into memory and parses PDF/DOCX data from bytes/`BytesIO`; it does not write user uploads to an application upload directory. Werkzeug may spool request bodies to its temporary directory and closes those request streams after handling the request. Render's ephemeral filesystem is therefore not used as durable storage. Saved writing history is stored in Atlas.

### Environment variables and secret locations

Backend settings read by Flask: `APP_ENV`, `SECRET_KEY`, `FLASK_DEBUG`, `PORT`, `CORS_ORIGINS`, `MAX_UPLOAD_MB`, `MONGODB_URI`, `MONGODB_DB_NAME`, `MONGODB_TIMEOUT_MS`, `LLM_PROVIDER`, `ANTHROPIC_API_KEY` (only for the optional Anthropic provider), `GEMINI_API_KEY`, `LLM_MODEL`, optional `LLM_FALLBACK_MODEL` (AI agent only), and `LLM_TIMEOUT_SECONDS`. Optional LanguageTool paths are `WRITEWISE_LANGUAGETOOL_JAR_DIR`, `LTP_PATH`, and `LTP_JAR_DIR_PATH`; the Render Docker image manages its cache internally.

Frontend-exposed build settings: `VITE_API_BASE_URL`, `VITE_APP_NAME`, and `VITE_MAX_UPLOAD_MB`. These are public bundle configuration, not secret storage. The checked-in `.env` files are ignored by Git; `.env.example` files contain placeholders only.

### Production limitation to resolve before public use

Saved writing history routes currently have no authentication or per-user authorization. Anyone who can reach the API can list or delete the shared saved history. Do not store sensitive user writing or expose the public service until access control is implemented or an equivalent access restriction is in place. The existing `users` model is not wired into authentication routes.
# Local Docker setup

This runs the existing Flask backend image and a multi-stage frontend image. The frontend is built with Node and served by Nginx; Nginx forwards `/api/*` to the Compose `backend` service over the private Compose network. MongoDB remains on MongoDB Atlas; no database container is started.

## Configure environment

Create `backend/.env` from the checked-in template:

```powershell
Copy-Item backend/.env.example backend/.env
```

Set the Atlas URI, AI provider key/model, and a strong local `SECRET_KEY` there as needed. Keep the file private: `.env` files are ignored by Git and excluded from Docker build contexts. Never put credentials in a `VITE_` variable; frontend variables are embedded in browser JavaScript. `backend/.env.example` contains placeholders and is safe to commit.

## Build and run

From the repository root:

```powershell
docker compose up --build
```

Open <http://localhost:8080>. The backend is also available at <http://localhost:5001/api/health>. Compose waits for the backend health check before starting the frontend. No source bind mounts are used, so rebuild after changing application code.

Useful commands:

```powershell
# Build without starting services
docker compose build

# Run in the background
docker compose up --build -d

# Follow service logs
docker compose logs -f

# Stop and remove containers and the Compose network
docker compose down

# Rebuild one service after changes
docker compose build frontend
docker compose up -d frontend
```

## Troubleshooting

- Check readiness with `docker compose ps` and inspect logs with `docker compose logs backend` or `docker compose logs frontend`.
- If the frontend loads but API calls fail, check `http://localhost:8080/api/health` and confirm the backend is healthy. Browser requests use the same-origin `/api` path; Nginx resolves `backend` using Compose DNS.
- If the backend reports Atlas or AI configuration errors, verify the values in `backend/.env`, Atlas IP access rules, and database credentials. Atlas connectivity requires an allowed client IP; the container does not run MongoDB.
- If a host port is already occupied, change the host side of `8080:80` or `5001:5001` in `docker-compose.yml`.
- After changing frontend build settings, run `docker compose build --no-cache frontend` because Vite bakes public `VITE_` settings into static assets.
