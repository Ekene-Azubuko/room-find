# Room Find

## Structure

```text
AGENTS.md                 Project instructions
README.md                 Setup and usage
.gitignore                Local file exclusions
compose.yaml              Local frontend, backend, and PostgreSQL services
.env.example              Docker Compose environment settings
frontend/                 Empty; reserved for a later increment
backend/
    app/
        __init__.py       Application factory
        routes.py         Health and registration routes
        db.py             SQLite connection management
    requirements.txt      Flask dependency
    Dockerfile            Flask development image
    .dockerignore         Exclude local data and secrets from builds
    .env.example          Reference environment settings
```

Git does not track empty directories. After cloning, run this from the repository root to recreate the frontend directory:

```sh
mkdir frontend
```

## Docker Compose setup

Prerequisites: Docker with the Compose plugin (included in Docker Desktop),
with the Docker engine running. From the repository root:

```sh
mkdir -p frontend
cp .env.example .env
```

Set `POSTGRES_PASSWORD` in the root `.env` to a local development password, then run:

```sh
docker compose up --build -d
docker compose ps
curl http://127.0.0.1:5000/api/health
```

- Frontend: http://localhost:3000 serves `frontend/` using Python's static HTTP
  server. The directory is still empty, so it shows an empty directory listing.
- Backend: http://localhost:5000 runs Flask with debug reload and mounted source.
- PostgreSQL: `localhost:5432` from the host, or `db:5432` from other containers.
  Database name, username, and password come from the root `.env`.

This is a local development setup. The backend still uses SQLite; this increment
adds PostgreSQL infrastructure without migrating registration or existing accounts.
SQLite data remains in `backend/instance/` through the backend bind mount.
PostgreSQL data persists in the `postgres_data` Docker volume. Its environment
settings initialize a new volume only; editing `.env` does not change existing
database credentials.

Check PostgreSQL or stop the services:

```sh
docker compose exec db sh -c 'pg_isready -h 127.0.0.1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
docker compose down
```

`docker compose down` preserves database data. Adding `--volumes` deletes the
PostgreSQL volume and its data.

## Local setup (without Docker)

Prerequisites: Python 3.9 or newer with pip and venv support. Use `python3` instead of `python` if required by your system.

From the repository root:

```sh
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m flask --app app:create_app run --debug
```

On Windows, replace the activation command with `.venv\Scripts\Activate.ps1` in PowerShell or `.venv\Scripts\activate.bat` in Command Prompt.

The debug server is for local development only. `backend/.env.example` documents reference values for `FLASK_APP` and `FLASK_DEBUG`; this scaffold does not automatically load `.env` files. The explicit CLI flags above configure the app and debug mode without a dotenv dependency.

## Check the API

With the server running, use another terminal:

```sh
curl http://127.0.0.1:5000/api/health
```

Expected response (HTTP 200):

```json
{"status":"ok"}
```

## Create a user

The backend automatically creates `backend/instance/room_find.sqlite` on startup.
This local SQLite database persists accounts across restarts and is ignored by Git.
No additional dependencies or environment variables are needed.

```sh
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"alex@example.com","password":"a-long-example-password"}'
```

Successful response (HTTP 201):

```json
{"user":{"id":1,"email":"alex@example.com"}}
```

IDs are assigned by the database. Emails are trimmed and lowercased, checked for
basic email format, and limited to 254 characters. Passwords must contain 8–128
characters and are stored only as salted hashes using Werkzeug (included with
Flask). Passwords and hashes are never included in registration responses.

Invalid JSON or invalid fields return HTTP 400 with an `error` message. A missing
JSON content type returns 415, and an existing email returns 409. Registration
creates an account only; login, sessions, and email verification are not implemented.
