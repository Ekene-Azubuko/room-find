# Room Find

## Docker setup

Install Docker with Docker Compose. Run these commands from the repository root.

```sh
cp -n .env.example .env
```

Edit `.env` and set `POSTGRES_PASSWORD` and `SECRET_KEY`. Use a URL-safe database
password and a random secret of at least 32 characters. Generate a secret with:

```sh
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

Build the app, apply database migrations, and start the services:

```sh
docker compose up -d --wait db
docker compose build backend frontend
docker compose run --rm backend python -m flask --app app:create_app db upgrade
docker compose up -d --wait backend frontend
```

Open **http://127.0.0.1:3000**. Nginx serves the built React frontend and forwards
`/api/*` requests to `backend:5000` inside Docker. PostgreSQL runs at `db:5432`
inside Docker and is accessible at `127.0.0.1:5432` from your computer.

After pulling changes:

```sh
docker compose exec backend python -m flask --app app:create_app db upgrade
docker compose restart backend
docker compose up -d --build frontend
```

Rebuild the backend image with `docker compose up -d --build backend` if its
dependencies or Dockerfile change. This setup uses Flask's development server.

Stop the app with `docker compose down`. Database records remain in the
`postgres_data` volume; adding `--volumes` deletes that data. Changing `.env`
does not update credentials in an existing database volume.

## Seed simulated data

After setup and migrations, add the four fictional roommate profiles:

```sh
docker compose exec backend python -m flask --app app:create_app seed-roommates
```

For a local backend, run this from `backend/` with its virtual environment and
environment variables configured:

```sh
python -m flask --app app:create_app seed-roommates
```

Seeding adds Maya, Jordan, Priya, and Elena with sample housing and lifestyle
answers. It is safe to repeat: existing demo profiles and edits are preserved.
Demo profiles cannot log in. Register your own account to browse them.

## Local setup alternative

Use Python 3.12, Node.js 22.12+, and PostgreSQL 17. You can run only PostgreSQL
through Docker using `docker compose up -d --wait db` after configuring `.env`.
Stop the Docker backend and frontend first if they are running:

```sh
docker compose stop backend frontend
```

In a terminal at the repository root, configure and start Flask:

```sh
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
export DATABASE_URL='postgresql+psycopg://room_find:replace-me@127.0.0.1:5432/room_find'
export SECRET_KEY='replace-with-a-generated-random-secret-at-least-32-characters'
export SESSION_COOKIE_SECURE=false
python -m flask --app app:create_app db upgrade
python -m flask --app app:create_app run --debug --port 5000
```

Replace the database name, username, and password with your PostgreSQL values.
URL-encode special characters in credentials. `backend/.env.example` documents
these variables; it is not loaded automatically. Run `db upgrade` again when
schema migrations are added.

In another terminal at the repository root, start Vite:

```sh
cd frontend
npm ci
npm run dev
```

Open **http://127.0.0.1:5173**. Vite forwards `/api/*` requests to Flask on port
5000. To use another backend port, set `API_PROXY_TARGET` in `frontend/.env`,
using `frontend/.env.example` as a reference. Use one browser hostname consistently
so session cookies are not split between `localhost` and `127.0.0.1`.

## Check health

Check through the Docker frontend or directly against a local Flask server:

```sh
# Docker frontend and its API proxy
curl -i http://127.0.0.1:3000/api/health

# Local Flask backend
curl -i http://127.0.0.1:5000/api/health
```

A healthy API and database return HTTP 200 with `{"status":"ok"}`. Database
connection failures return HTTP 503. This check does not verify that migrations
have been applied.

For Docker service status and logs:

```sh
docker compose ps
docker compose logs --tail=50 backend frontend db
```

## Run tests

**Backend:** use the dedicated disposable PostgreSQL service. From the repository
root, with Python 3.12 installed:

```sh
docker compose -p room-find-tests -f compose.test.yaml up -d --wait
(
  cd backend
  python3.12 -m venv .venv
  source .venv/bin/activate
  python -m pip install -r requirements-dev.txt
  export TEST_DATABASE_URL='postgresql+psycopg://room_find_test:test-only-password@127.0.0.1:55439/room_find_test'
  python -m pytest
)
docker compose -p room-find-tests -f compose.test.yaml down
```

Tests apply migrations and clear the test database between cases. Use only the
specified test service, and do not run concurrent suites against it. GitHub Actions
also runs backend tests on pushes and pull requests to `main`.

**Frontend:** from the repository root:

```sh
cd frontend
npm ci
npm test
npm run build
```

`npm test` runs the existing client, filtering, and lifestyle tests. The build
checks TypeScript and generates the frontend assets.

For a manual check, register a disposable account, save and reload profile answers,
complete setup, browse and filter demo profiles, then sign out and sign in again.
Check the forms and profile comparisons at desktop and mobile widths.

## DB schema

![Room Find database schema](docs/db-schema.png)

| Table | Purpose | Relationship |
| --- | --- | --- |
| `users` | Credentials, profile details, and onboarding status | Primary key: `id` |
| `housing_preferences` | Location, budget, move-in, lease, and requirement flags | `user_id` references `users.id`; zero or one row per user |
| `lifestyle_preferences` | Personal answers, roommate expectations, and importance | `user_id` references `users.id`; one row per answered question, keyed by `(user_id, question_key)` |

Deleting a user cascades to their preferences. Null answers mean unanswered;
`no_preference` means explicitly unrestricted. `legacy_answers` archives older
combined answers. Question definitions live in Python. Alembic separately tracks
the applied migration in `alembic_version`.

The [models](backend/app/models.py) define the tables, and
[migrations](backend/migrations/versions/) version schema changes. To regenerate
the diagram from its [DOT file](docs/db-schema.dot), install Graphviz and run:

```sh
dot -Tpng -Gdpi=150 docs/db-schema.dot -o docs/db-schema.png
```

## Folder structure

```text
room-find/
├── .env.example                 # Docker configuration reference
├── compose.yaml                 # App services and database volume
├── compose.test.yaml            # Isolated test database
├── backend/
│   ├── app/__init__.py          # Flask application factory
│   ├── app/models.py            # Database models
│   ├── app/                     # API routes, validation, and demo seeding
│   ├── migrations/              # Database migrations
│   ├── tests/                   # Backend tests
│   └── requirements*.txt        # Python dependencies
├── frontend/
│   ├── src/                     # React pages, components, and API client
│   ├── public/                  # Images and favicon
│   ├── tests/                   # Frontend tests
│   ├── package.json             # Dependencies and npm commands
│   └── vite.config.ts           # Local development server and API proxy
├── deploy/nginx.conf            # Docker frontend serving and API proxy
├── docs/                        # API reference and diagrams
└── .github/workflows/backend.yml # Backend CI
```
