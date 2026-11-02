# Room Find

A small Flask API using PostgreSQL 17. Use Python 3.12 (the Docker and CI version).
`frontend/` is intentionally empty; recreate it with `mkdir -p frontend` after cloning.

## Structure

- `backend/app/__init__.py`: application factory and blueprint registration.
- `backend/app/health/routes.py`, `backend/app/auth/routes.py`,
  `backend/app/profile/routes.py`, `backend/app/preferences/routes.py`,
  `backend/app/onboarding/routes.py`: API routes.
- `backend/app/validation.py`, `errors.py`: shared input validation and JSON errors.
- `backend/app/extensions.py`, `models.py`: database extensions and models.
- `backend/migrations/`: reviewed, versioned Alembic schema migrations.
- `backend/tests/`: isolated PostgreSQL API and constraint tests.

## Docker development setup

```sh
mkdir -p frontend
cp -n .env.example .env
# Edit .env: set POSTGRES_PASSWORD and a random SECRET_KEY (at least 32 characters).
# Generate the secret with: python3 -c 'import secrets; print(secrets.token_hex(32))'
docker compose up -d db
docker compose build backend
docker compose run --rm backend python -m flask --app app:create_app db upgrade
docker compose up -d --wait backend frontend
curl http://127.0.0.1:3000/api/health
```

Use one browser origin: `http://localhost:3000`. The existing `frontend` service
now runs Nginx and forwards `/api/` unchanged to `backend:5000`; static files remain
empty and there is no UI. Direct Flask access at `http://localhost:5000` remains
available for local debugging. Do not mix localhost and 127.0.0.1 cookie jars.
No CORS configuration is needed or enabled for the same-origin path.

PostgreSQL is at `db:5432` inside Compose and `127.0.0.1:5432` from the host. Use
URL-safe database credentials in Compose; URL-encode special characters for a
manually set URL. Startup order is healthy PostgreSQL, then healthy Flask, then
Nginx. `/api/health` checks the PostgreSQL connection and returns JSON 503 if it
cannot connect; it does not create tables or apply migrations.

`FLASK_DEBUG=0` is the default; set it to 1 only for intentional local debugging.
The Flask development server is **not a production server**. An HTTPS deployment
needs external TLS termination and a production WSGI server, with debug off and
`SESSION_COOKIE_SECURE=true`. Local Compose supplies HTTP only.

PostgreSQL persists in the existing `postgres_data` volume. `docker compose down`
preserves it; do not add `--volumes` unless you intend to delete its data. Changing
`.env` does not change credentials in an already initialized volume.

## Local setup

```sh
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
export DATABASE_URL='postgresql+psycopg://room_find:replace-me@127.0.0.1:5432/room_find'
export SECRET_KEY='replace-with-a-generated-random-secret-at-least-32-characters'
export SESSION_COOKIE_SECURE=false
python -m flask --app app:create_app db upgrade
python -m flask --app app:create_app run --debug
```

For this direct local server, use port 5000 instead of 3000 in the API examples.
PostgreSQL must already be running (for example, `docker compose up -d db` from
the repository root after configuring `.env`). Replace the example credentials. `backend/.env.example` is a reference, not an
automatically loaded configuration file. An explicit `postgresql+psycopg` URL is
required. Startup never creates tables and never falls back to SQLite.
Run `db upgrade` after pulling schema changes; repeating it is safe. To generate
a future migration, run `python -m flask --app app:create_app db migrate -m 'description'`,
review the generated file, and test it before applying it. Downgrades remove data;
do not run them against development accounts as a routine setup step.

## Data preservation

The previous implementation stored accounts in `backend/instance/room_find.sqlite`.
No SQLite database files/accounts were present in this checkout when PostgreSQL
was introduced, so no import was necessary or performed. No existing database
files or Docker volumes were deleted. Schema migrations **do not copy SQLite
accounts**. If you have a SQLite copy elsewhere, keep it unchanged and arrange a
separate validated, transactional import before switching that installation;
preserve IDs, normalized emails, password hashes and any original timestamps,
reject normalized-email conflicts, and advance the PostgreSQL ID sequence.

`User` has a one-to-one `HousingPreference` and one-to-many `LifestylePreference`.
Housing budgets use `NUMERIC(10,2)`; PostgreSQL enforces nonnegative budgets,
ordered bounds, positive leases, unique keys and foreign keys. User deletion
cascades to both preference tables. Timestamps are timezone-aware UTC values.
Lifestyle values reserve NULL for unanswered and `no_preference` for a deliberate
lack of preference. Lifestyle routes use the shared initial questionnaire below.

## API

Use a cookie jar and pass `X-CSRF-Token` on all POST/PATCH/PUT/DELETE requests,
including registration and login. Obtain a **fresh token after login or logout**:
these operations clear all previous session state. CSRF failures return HTTP 400.

```sh
curl http://127.0.0.1:3000/api/health
TOKEN=$(curl -s -b cookies.txt -c cookies.txt http://127.0.0.1:3000/api/auth/csrf | python3 -c 'import json,sys; print(json.load(sys.stdin)["csrf_token"])')
curl -b cookies.txt -c cookies.txt -X POST http://127.0.0.1:3000/api/auth/register \
  -H 'Content-Type: application/json' -H "X-CSRF-Token: $TOKEN" \
  -d '{"email":"alex@example.com","password":"a-long-example-password"}'
curl -b cookies.txt -c cookies.txt -X POST http://127.0.0.1:3000/api/auth/login \
  -H 'Content-Type: application/json' -H "X-CSRF-Token: $TOKEN" \
  -d '{"email":"alex@example.com","password":"a-long-example-password"}'
TOKEN=$(curl -s -b cookies.txt -c cookies.txt http://127.0.0.1:3000/api/auth/csrf | python3 -c 'import json,sys; print(json.load(sys.stdin)["csrf_token"])')
curl -b cookies.txt http://127.0.0.1:3000/api/auth/me
curl -b cookies.txt -c cookies.txt -X POST http://127.0.0.1:3000/api/auth/logout \
  -H "X-CSRF-Token: $TOKEN"
```

`GET /api/auth/csrf` returns `{"csrf_token":"..."}` and is not cacheable.
`POST /api/auth/login` and `GET /api/auth/me` return the same safe `user` identity
as registration; missing/invalid/expired sessions return JSON 401. Incorrect
passwords and unknown emails return the identical 401 error.
`POST /api/auth/logout` returns `{"message":"Logged out."}` and clears the cookie.

Sessions contain only a user ID, permanence flag and (when obtained) a CSRF token.
Cookies are HttpOnly, SameSite=Lax, and expire after 12 hours without sliding
refresh. Set `SESSION_COOKIE_SECURE=true` for HTTPS deployment; use false only
for local HTTP. Keep a randomly generated `SECRET_KEY` outside Git, stable across
workers/restarts. Changing it invalidates existing sessions. Flask signed-cookie
logout removes access for that browser; it does not centrally revoke a copied
cookie before expiry. Keep API and client same-origin for this cookie setup.

Healthy API/database connectivity returns `{"status":"ok"}`. Registration returns HTTP 201 with
`{"user":{"id":1,"email":"alex@example.com"}}`. Emails are trimmed/lowercased,
limited to 254 characters, and checked for basic format. Passwords must contain
8–128 characters and are stored as salted Werkzeug hashes. Responses never
include passwords/hashes. Registration does not log in the user.

Invalid JSON/fields return 400, non-JSON content types 415, duplicate normalized
emails 409. HTTP errors (including 404/405) use `{"error":"message"}`; 405 retains
its `Allow` header. Blueprints are registered once in `create_app()`.

## Isolated backend tests

From the repository root:

```sh
docker compose -p room-find-tests -f compose.test.yaml up -d --wait
cd backend
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
unset DATABASE_URL
export TEST_DATABASE_URL='postgresql+psycopg://room_find_test:test-only-password@127.0.0.1:55439/room_find_test'
python -m pytest
cd ..
docker compose -p room-find-tests -f compose.test.yaml down
```

The test service uses temporary memory-backed storage and no development volume.
Tests require both database and role to be named `room_find_test`, reject the
configured development target, apply migrations, and clear only test tables.
Do not point this role/database at real data. Do not run concurrent suites against
one test database. Tests cover empty-schema/repeated upgrades, actual PostgreSQL
constraints, rollback, relationships, hashing, validation and persistence.
GitHub Actions runs the full suite on Python 3.12 with its own PostgreSQL 17 service.
Main pushes and PRs run this job.

## Profile API

`GET /api/profile` returns `{"profile":{...}}` for the authenticated user, including
id, email, full_name, bio, onboarding_completed_at, created_at and updated_at.
Timestamps are ISO 8601 UTC strings; absent values are JSON null. Credentials are
never serialized. `PATCH /api/profile` accepts only `full_name` and `bio`:

```sh
# After login, fetch a fresh TOKEN as shown above.
curl -b cookies.txt -c cookies.txt -X PATCH http://127.0.0.1:3000/api/profile \
  -H 'Content-Type: application/json' -H "X-CSRF-Token: $TOKEN" \
  -d '{"full_name":"Alex Smith","bio":"Looking for a quiet apartment."}'
curl -b cookies.txt http://127.0.0.1:3000/api/profile
```

Omitted fields are preserved. Names are trimmed, nonblank when supplied, and at
most 100 characters; biographies are at most 1,000 characters. Explicit null
clears either field; clearing a required name resets onboarding completion. Invalid fields return 400
without saving any changes. IDs, email, credentials and timestamps are read-only;
no submitted ID selects a user. Saves change `updated_at` only when data changes.
Authentication failures return 401 (provide valid CSRF when testing PATCH auth).
Completion is explicit; see the onboarding endpoints below.

## Housing preferences API

`GET /api/preferences/housing` returns `{"housing":null}` before the first save,
then `{"housing":{...}}`. `PATCH /api/preferences/housing` creates the session user's
single row on first save and updates it on subsequent saves. No URL/body user ID
can select another account. The response contains the answer fields below, four
requirement flags, and a UTC `updated_at`; unchanged saves retain that timestamp.

```sh
# Use the fresh post-login TOKEN and cookie jar from the authentication example.
curl -b cookies.txt -c cookies.txt -X PATCH http://127.0.0.1:3000/api/preferences/housing \
  -H 'Content-Type: application/json' -H "X-CSRF-Token: $TOKEN" \
  -d '{"city":"Seattle","budget_min":"900.00","budget_max":"1500.00","move_in_date":"2027-02-01","lease_months":12,"budget_is_requirement":true}'
curl -b cookies.txt http://127.0.0.1:3000/api/preferences/housing
```

- `city`: trimmed nonblank text, at most 100 characters, or null.
- `budget_min` / `budget_max`: **your monthly rent share in USD**, supplied as JSON
  numbers or decimal strings. Values must be finite, 0–99,999,999.99, with at most
  two decimal places. Decimal arithmetic is exact; extra precision is rejected,
  never silently rounded. Responses always use two-decimal strings or null.
- `move_in_date`: a valid `YYYY-MM-DD` date or null.
- `lease_months`: a positive integer (at most 2,147,483,647) or null; strings,
  Boolean values and fractional numbers are rejected.
- `city_is_requirement`, `budget_is_requirement`, `move_in_is_requirement`,
  `lease_is_requirement`: actual JSON Booleans, default false. True requires the
  corresponding answer. For budget, at least one bound must exist; zero is valid.

PATCH preserves omitted fields and allows explicit nulls for answers. Validation
uses the **merged saved and incoming state**: a new minimum cannot exceed an
existing maximum, and clearing a required answer requires setting its flag false
in the same request (unless another budget bound remains). Unknown/read-only
fields, invalid types and inconsistent states return JSON 400 without saving any
changes. CSRF is required; unauthenticated requests with valid CSRF return 401.
Concurrent saves are serialized per user so first saves create only one row.

No matching, chat or frontend UI is implemented.

## Lifestyle preferences API

All three routes require authentication; PUT also requires `X-CSRF-Token`.

- `GET /api/preferences/lifestyle/questions` returns `{"questions":[...]}` in
  display order, with question_key, question, roommate_question, own_answers,
  roommate_answers, display_order and required_for_onboarding.
- `GET /api/preferences/lifestyle` returns `{"answers":[]}` before any saves,
  then saved answer objects in questionnaire order.
- `PUT /api/preferences/lifestyle/<question_key>` replaces one **complete** answer
  and returns `{"answer":{...}}` (HTTP 200 for both creation and replacement).
  Required body fields: own_answer, roommate_answer, is_requirement. Responses
  also include question_key and updated_at. Other question rows are unchanged.

No final questionnaire specification was present in the checkout. This initial
set uses single-choice categories that fit the existing one-answer-per-column
schema; pet presence deliberately avoids multi-select pet species. All five
questions are initially required for onboarding. Definitions live in
`backend/app/preferences/questions.py` and are shared with validation.

| Stable key | Allowed own answers | Allowed roommate answers |
| --- | --- | --- |
| sleep_schedule | early, late, flexible | own choices plus no_preference |
| cleanliness | very_tidy, moderately_tidy, relaxed | own choices plus no_preference |
| smoking | non_smoker, smoker | own choices plus no_preference |
| guests | rarely, sometimes, often | own choices plus no_preference |
| pets | has_pets, no_pets | own choices plus no_preference |

```sh
curl -b cookies.txt -c cookies.txt -X PUT http://127.0.0.1:3000/api/preferences/lifestyle/sleep_schedule \
  -H 'Content-Type: application/json' -H "X-CSRF-Token: $TOKEN" \
  -d '{"own_answer":"early","roommate_answer":"no_preference","is_requirement":false}'
```

NULL means unanswered/cleared; `no_preference` is a deliberate roommate preference
and is not an own-answer choice. `is_requirement` applies only to the roommate
answer and must be false for null or no_preference. Unknown keys return 404;
missing/unknown fields, invalid types/choices and inconsistent flags return 400.
Failed database commits roll back and return a safe JSON 503 error. User IDs and
server timestamps cannot be supplied. There is no bulk-save endpoint.


## Onboarding API

`GET /api/onboarding` requires authentication and returns
`{"onboarding":{"completed":false,"onboarding_completed_at":null,"eligible":false,
"missing_fields":["profile.full_name", "housing.city", "lifestyle.sleep_schedule.own_answer"],
"errors":{"profile.full_name":"An answer is required."}}}` (illustrative subset).
Missing entries identify every unanswered required field; errors also identify
invalid saved fields/questions. Reading progress never marks onboarding complete.

`POST /api/onboarding/complete` requires authentication and CSRF. Send no body or
an empty JSON object. It validates saved answers, returning HTTP 400 with `error`
and the full `onboarding` state when incomplete/invalid. An eligible request
returns HTTP 200 with `onboarding.completed=true` and an ISO 8601 UTC timestamp.
Repeated successful requests preserve the original timestamp. Clients cannot
supply completion flags, timestamps or user IDs.

```sh
curl -b cookies.txt http://127.0.0.1:3000/api/onboarding
curl -b cookies.txt -c cookies.txt -X POST http://127.0.0.1:3000/api/onboarding/complete \
  -H "X-CSRF-Token: $TOKEN"
```

No separate onboarding specification was present, so the centralized defaults in
`backend/app/onboarding/state.py` require a nonblank full_name, **all five housing
answers** (including both budget bounds), and own_answer plus roommate_answer
for every required question. Bio is optional. `no_preference` counts as an answered
roommate preference; null never does. All saved values and requirement flags must
also satisfy their existing validators.

Users may edit after completion. Valid edits retain the timestamp; clearing a
required profile, housing or lifestyle answer clears the timestamp **in the same
transaction**. Clearing optional bio does not reset completion. Requirement flags
must still be cleared with absent/no-preference answers; invalid edits save
nothing and retain the existing completion state. Restoring answers makes the
user eligible again but requires another explicit completion request. Progress
is derived from current data, so corrupt/legacy invalid data is reported as
ineligible rather than trusted solely because a timestamp exists.
## Configuration and API reference

Root `.env` supplies POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD and SECRET_KEY;
Compose constructs DATABASE_URL using `db:5432`. For direct local Flask use,
export DATABASE_URL and SECRET_KEY explicitly. SESSION_COOKIE_SECURE defaults to
false for local HTTP; FLASK_DEBUG defaults to 0. The session lifetime is 12 hours
with no sliding refresh, HttpOnly and SameSite=Lax. Keep SECRET_KEY stable across
workers/restarts. No real secrets belong in `.env.example` or version control.

See [docs/API.md](docs/API.md) for the complete method/path reference and response
examples. All changes through onboarding reuse the existing migration; no new
schema revision was needed for branches 7–9. The initial questionnaire and the
required-data defaults are explicitly provisional product choices. This increment
stops after backend integration: no matching, chat, email verification, password
recovery or frontend UI.
