import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useApi } from "../api/ApiContext";
import { useAuth } from "../api/AuthContext";
import { ApiError } from "../api/client";
import { Header } from "../components/Header";
import { Icon } from "../components/Icon";

/** Welcome authenticated users while the matching page is being built. */
export function Home() {
  const api = useApi();
  const auth = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  /** Clear the server session before returning to the login page. */
  async function logout() {
    setBusy(true);
    try {
      await api.logout();
      auth.setUser(null);
      navigate("/login", { replace: true });
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        auth.setUser(null);
        navigate("/login", { replace: true });
      } else {
        setError(error instanceof Error ? error.message : "Unable to sign out.");
      }
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Header>
        <button className="text-button" disabled={busy} onClick={logout}>
          {busy ? "Signing out…" : "Sign out"}
        </button>
      </Header>
      <main className="construction-page">
        <div className="construction-icon">
          <Icon name="construction" />
        </div>
        <span className="eyebrow-pill">A GOOD THING IS TAKING SHAPE</span>
        <h1>
          A little work.
          <br />A lot to look forward to.
        </h1>
        <div className="construction-label">
          <span />
          Page under construction
        </div>
        <p>
          You’re signed in. We’re making room for your next chapter.
          <br />
          Your roommate matching page is on its way.
        </p>
        <Link className="button primary" to="/setup">
          View your profile
          <Icon name="arrow" />
        </Link>
        {error && (
          <div className="error-message" role="alert">
            {error}
          </div>
        )}
      </main>
    </>
  );
}
