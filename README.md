# Room Find

## Structure

```text
AGENTS.md                 Project instructions
README.md                 Setup and usage
.gitignore                Local file exclusions
frontend/                 Empty; reserved for a later increment
backend/
    app/
        __init__.py       Application factory
        routes.py         API blueprint and health route
    requirements.txt      Flask dependency
    .env.example          Reference environment settings
```

Git does not track empty directories. After cloning, run this from the repository root to recreate the frontend directory:

```sh
mkdir frontend
```

## Local setup

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
