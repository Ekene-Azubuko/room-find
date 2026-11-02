"""Verify the real Compose/proxy stack using only a generated disposable project."""
import http.cookiejar
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]


class Browser:
    """Keep real HTTP cookies and a CSRF token for one isolated browser."""

    def __init__(self, base_url):
        """Create an opener with its own in-memory cookie jar."""
        self.base_url = base_url
        self.cookies = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookies))
        self.token = None
        self.last_headers = None

    def request(self, method, path, data=None, expected=200, csrf=True):
        """Send JSON and verify the status without logging cookies or credentials."""
        headers = {}
        if csrf and self.token:
            headers["X-CSRF-Token"] = self.token
        body = None
        if data is not None:
            body = json.dumps(data).encode()
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(self.base_url + path, data=body, headers=headers, method=method)
        try:
            response = self.opener.open(request, timeout=10)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            self.last_headers = response.headers
            payload = json.load(response)
            assert response.status == expected, f"{method} {path}: expected {expected}, got {response.status}: {payload}"
            return payload

    def fresh_csrf(self):
        """Fetch the token associated with the current cookie session."""
        self.token = self.request("GET", "/api/auth/csrf")["csrf_token"]
        return self.token


def wait_ready(browser):
    """Wait briefly for the real proxy and PostgreSQL readiness path."""
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            if browser.request("GET", "/api/health") == {"status": "ok"}:
                return
        except (OSError, AssertionError, ValueError):
            time.sleep(1)
    raise RuntimeError("Proxy did not become ready within 60 seconds.")


def save_complete_account(browser, credentials):
    """Run the complete onboarding flow through HTTP, including CSRF rotation."""
    browser.fresh_csrf()
    cookie = browser.last_headers.get("Set-Cookie", "")
    assert "HttpOnly" in cookie and "SameSite=Lax" in cookie and "Secure" not in cookie
    rejected = browser.request("POST", "/api/auth/register", credentials, expected=400, csrf=False)
    assert rejected == {"error": "A valid CSRF token is required."}
    assert browser.request("POST", "/api/auth/register", credentials, expected=201)["user"]["email"] == credentials["email"]
    previous = browser.token
    browser.request("POST", "/api/auth/login", credentials)
    assert browser.fresh_csrf() != previous
    browser.request("PATCH", "/api/profile", {"full_name": "HTTP Smoke User"})
    browser.request("PATCH", "/api/preferences/housing", {
        "city": "Seattle", "budget_min": "900.00", "budget_max": "1500.00",
        "move_in_date": "2027-02-01", "lease_months": 12})
    questions = browser.request("GET", "/api/preferences/lifestyle/questions")["questions"]
    for question in questions:
        browser.request("PUT", "/api/preferences/lifestyle/" + question["question_key"], {
            "own_answer": question["own_answers"][0], "roommate_answer": "no_preference", "is_requirement": False})
    progress = browser.request("GET", "/api/onboarding")["onboarding"]
    assert progress["eligible"] and not progress["completed"]
    complete = browser.request("POST", "/api/onboarding/complete")
    assert complete["onboarding"]["completed"]
    assert browser.request("POST", "/api/onboarding/complete") == complete
    return {path: browser.request("GET", path) for path in (
        "/api/profile", "/api/preferences/housing", "/api/preferences/lifestyle", "/api/onboarding")}


def check_isolation(base_url, owner):
    """Prove that a second real browser cannot read or write the owner's answers."""
    other = Browser(base_url)
    other.fresh_csrf()
    credentials = {"email": "other@example.com", "password": secrets.token_urlsafe(24)}
    other.request("POST", "/api/auth/register", credentials, expected=201)
    other.request("POST", "/api/auth/login", credentials)
    other.fresh_csrf()
    assert other.request("GET", "/api/preferences/housing?user_id=1") == {"housing": None}
    assert other.request("GET", "/api/preferences/lifestyle") == {"answers": []}
    assert not other.request("GET", "/api/onboarding")["onboarding"]["completed"]
    rejected = other.request("PATCH", "/api/profile", {"user_id": 1, "full_name": "Hijacked"}, expected=400)
    assert "user_id" in rejected["error"]
    assert owner.request("GET", "/api/profile")["profile"]["full_name"] == "HTTP Smoke User"


def main():
    """Build, migrate, exercise, restart and remove only this disposable test stack."""
    project = "room-find-smoke-" + uuid.uuid4().hex[:12]
    values = {"POSTGRES_DB": "room_find_integration", "POSTGRES_USER": "room_find_integration",
              "POSTGRES_PASSWORD": secrets.token_hex(24), "SECRET_KEY": secrets.token_hex(32),
              "SESSION_COOKIE_SECURE": "false", "FLASK_DEBUG": "0"}
    with tempfile.TemporaryDirectory(prefix="room-find-smoke-") as directory:
        env_file = Path(directory) / "integration.env"
        env_file.write_text("".join(f"{key}={value}\n" for key, value in values.items()))
        env_file.chmod(0o600)
        command = ["docker", "compose", "--env-file", str(env_file), "-p", project,
                   "-f", str(ROOT / "compose.yaml"), "-f", str(ROOT / "compose.integration.yaml")]
        environment = {**os.environ, **values}

        def compose(*args):
            """Run Compose with isolated credentials and without printing environment values."""
            return subprocess.check_output(command + list(args), cwd=ROOT, env=environment, text=True).strip()

        def sql(query):
            """Read database state directly inside this project's PostgreSQL service."""
            return compose("exec", "-T", "db", "psql", "-U", values["POSTGRES_USER"],
                           "-d", values["POSTGRES_DB"], "-Atc", query)

        try:
            compose("up", "-d", "--build", "--wait")
            address = compose("port", "frontend", "3000")
            browser = Browser("http://" + address)
            wait_ready(browser)
            compose("exec", "-T", "backend", "python", "-c",
                    "from app import create_app; from app.extensions import db; "
                    "app=create_app(); ctx=app.app_context(); ctx.push(); "
                    "assert db.engine.url.host == 'db'; assert not app.debug; "
                    "assert len(app.secret_key) >= 32; "
                    "assert app.permanent_session_lifetime.total_seconds() == 43200; "
                    "assert app.config['SESSION_COOKIE_HTTPONLY']; "
                    "assert app.config['SESSION_COOKIE_SAMESITE'] == 'Lax'; "
                    "assert not app.config['SESSION_REFRESH_EACH_REQUEST']")
            assert sql("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'") == "0"
            print("PASS: actual Compose db connectivity; normal startup creates no tables", flush=True)
            for _ in range(2):
                compose("exec", "-T", "backend", "python", "-m", "flask", "--app", "app:create_app", "db", "upgrade")
            compose("exec", "-T", "backend", "python", "-m", "flask", "--app", "app:create_app", "db", "check")
            assert sql("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'") == "4"
            print("PASS: empty-database migration, repeat upgrade and schema drift check", flush=True)
            credentials = {"email": "smoke@example.com", "password": secrets.token_urlsafe(24)}
            snapshots = save_complete_account(browser, credentials)
            check_isolation(browser.base_url, browser)
            browser.request("POST", "/api/auth/logout")
            assert browser.request("GET", "/api/auth/me", expected=401) == {"error": "Authentication required."}
            browser.fresh_csrf()
            browser.request("POST", "/api/auth/login", credentials)
            browser.fresh_csrf()
            for path, saved in snapshots.items():
                assert browser.request("GET", path) == saved
            print("PASS: real proxy cookies/CSRF, full onboarding, isolation, logout and re-login", flush=True)
            compose("restart", "db", "backend", "frontend")
            # Docker may assign a new ephemeral host port when the proxy restarts.
            browser.base_url = "http://" + compose("port", "frontend", "3000")
            wait_ready(browser)
            for path, saved in snapshots.items():
                assert browser.request("GET", path) == saved
            assert sql("SELECT count(*) FROM users") == "2"
            assert sql("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'") == "4"
            print("PASS: records and signed sessions survive service restarts without deleting the volume", flush=True)
            browser.request("PATCH", "/api/profile", {"full_name": "Updated HTTP User"})
            assert browser.request("GET", "/api/onboarding") == snapshots["/api/onboarding"]
            browser.request("PUT", "/api/preferences/lifestyle/sleep_schedule", {
                "own_answer": None, "roommate_answer": "no_preference", "is_requirement": False})
            state = browser.request("GET", "/api/onboarding")["onboarding"]
            assert not state["completed"] and state["onboarding_completed_at"] is None
            assert state["missing_fields"] == ["lifestyle.sleep_schedule.own_answer"]
            print("PASS: valid edits preserve completion; clearing required answers resets it", flush=True)
            environment["SESSION_COOKIE_SECURE"] = "true"
            compose("up", "-d", "--force-recreate", "--no-deps", "--wait", "backend", "frontend")
            secure_browser = Browser("http://" + compose("port", "frontend", "3000"))
            secure_browser.fresh_csrf()
            assert "Secure" in secure_browser.last_headers.get("Set-Cookie", "")
            # A browser must withhold HTTPS-only cookies over this local HTTP path.
            rejected = secure_browser.request("POST", "/api/auth/login", credentials, expected=400)
            assert rejected == {"error": "A valid CSRF token is required."}
            print("PASS: environment-based Secure cookies are issued and withheld over HTTP", flush=True)
        finally:
            # The project name is generated here; this never targets development volumes.
            compose("down", "--volumes", "--remove-orphans")


if __name__ == "__main__":
    main()
