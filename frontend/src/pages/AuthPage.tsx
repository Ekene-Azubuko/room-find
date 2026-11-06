import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useApi } from "../api/ApiContext";
import { useAuth } from "../api/AuthContext";
import { Header } from "../components/Header";
import { Icon } from "../components/Icon";

/** Present matching registration and login forms backed by the real cookie session. */
export function AuthPage({ register = false }: { register?: boolean }) {
  const api = useApi();
  const auth = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [visible, setVisible] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [created, setCreated] = useState(false);

  /** Register once, then sign in; a failed login never repeats account creation. */
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (register && password !== confirm) {
      setError("Your passwords do not match.");
      return;
    }
    setBusy(true);
    try {
      const credentials = { email: email.trim(), password };
      if (register && !created) {
        await api.register(credentials);
        setCreated(true);
      }
      const { user } = await api.login(credentials);
      auth.setUser(user);
      navigate(register ? "/setup" : "/app", { replace: true });
    } catch (error) {
      setError(error instanceof Error ? error.message : "Please try again.");
    } finally {
      setBusy(false);
    }
  }
  if (auth.user) return <Navigate to={register ? "/setup" : "/app"} replace />;
  return (
    <>
      <Header>
        <span className="header-muted">
          {register ? "Already have an account?" : "New to Roomly?"}
        </span>
        <Link className="header-link" to={register ? "/login" : "/register"}>
          {register ? "Sign in" : "Create a profile"}
        </Link>
      </Header>
      <main className="auth-layout">
        <section className="auth-story">
          <div className="eyebrow-pill">
            <Icon name="sparkles" />A little more you. A little more home.
          </div>
          <h1>
            {register ? (
              <>
                Your next chapter
                <br />
                starts with a<br />
                <em>good fit.</em>
              </>
            ) : (
              <>
                Your people.
                <br />
                Your place.
                <br />
                <em>Welcome back.</em>
              </>
            )}
          </h1>
          <p>
            Shared spaces work better with shared understanding. Find someone
            who feels like home.
          </p>
          <div className="auth-portraits">
            <img src="/images/jordan.jpg" alt="Example roommate portrait" />
            <img src="/images/maya.jpg" alt="Example roommate portrait" />
            <div className="auth-photo-note">
              <Icon name="heart" />
              Better together.
            </div>
          </div>
        </section>
        <section className="auth-form-section">
          <span className="step-label">
            {register ? "LET’S GET STARTED" : "MAKE YOURSELF AT HOME"}
          </span>
          <h2>{register ? "Create your account" : "Good to see you again"}</h2>
          <p>
            {register
              ? "First, a place to save your profile. Then, let’s get to know you."
              : "Sign in to pick up right where you left off."}
          </p>
          <form className="surface auth-form" onSubmit={submit}>
            <fieldset disabled={busy || auth.loading}>
              <label>
                Email address
                <input
                  type="email"
                  name="email"
                  autoComplete="email"
                  maxLength={254}
                  required
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@example.com"
                />
              </label>
              <label>
                Password
                <div className="password-input">
                  <input
                    name="password"
                    type={visible ? "text" : "password"}
                    autoComplete={
                      register ? "new-password" : "current-password"
                    }
                    minLength={8}
                    maxLength={128}
                    required
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder={
                      register ? "Create a password" : "Enter your password"
                    }
                  />
                  <button
                    type="button"
                    aria-label={visible ? "Hide password" : "Show password"}
                    aria-pressed={visible}
                    onClick={() => setVisible(!visible)}
                  >
                    <Icon name="eye" />
                  </button>
                </div>
                {register && (
                  <span className="field-hint">Use 8–128 characters.</span>
                )}
              </label>
              {register && (
                <label>
                  Confirm password
                  <input
                    name="confirmPassword"
                    type={visible ? "text" : "password"}
                    autoComplete="new-password"
                    minLength={8}
                    maxLength={128}
                    required
                    value={confirm}
                    onChange={(event) => setConfirm(event.target.value)}
                    placeholder="Enter your password again"
                  />
                </label>
              )}
              {error && (
                <div className="error-message" role="alert">
                  {created &&
                    "Your account was created. Please sign in to continue. "}
                  {error}
                </div>
              )}
              <button className="button primary full-width" type="submit">
                {busy
                  ? register
                    ? "Creating your account…"
                    : "Signing in…"
                  : register
                    ? "Create account"
                    : "Sign in"}
                <Icon name="arrow" />
              </button>
            </fieldset>
            <div className="form-security">
              <Icon name="lock" />
              Your answers are private.
            </div>
          </form>
          <p className="auth-switch">
            {register
              ? "Already found us?"
              : "Looking for your kind of roommate?"}{" "}
            <Link to={register ? "/login" : "/register"}>
              {register ? "Sign in" : "Create your profile"}
            </Link>
          </p>
        </section>
      </main>
    </>
  );
}
