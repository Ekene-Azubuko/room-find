import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../api/AuthContext";
import { useApi } from "../api/ApiContext";
import { ApiError } from "../api/client";
import { Icon } from "./Icon";

/** Show discovery navigation and an accessible account menu on both new pages. */
export function DiscoverHeader() {
  const auth = useAuth();
  const api = useApi();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  /** Clear the cookie session before returning to sign in. */
  async function logout() {
    setBusy(true);
    setError("");
    try {
      await api.logout();
      auth.setUser(null);
      navigate("/login", { replace: true });
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        auth.setUser(null);
        navigate("/login", { replace: true });
      } else
        setError(
          error instanceof Error ? error.message : "Unable to sign out.",
        );
    } finally {
      setBusy(false);
    }
  }
  return (
    <header className="discover-header">
      <Link className="brand" to="/app" aria-label="Roomly discovery">
        <span className="brand-icon">
          <Icon name="home" />
        </span>
        Roomly
      </Link>
      <nav aria-label="Main navigation">
        <Link className="active" to="/app" aria-current="page">
          <Icon name="search" />
          Discover
        </Link>
        <span className="future-nav" title="Connections are coming soon">
          <Icon name="heart" />
          Connections <small>Soon</small>
        </span>
      </nav>
      <details className="account-menu">
        <summary>
          <span className="account-avatar">
            {auth.user?.email[0].toUpperCase()}
          </span>
          <span>Your account</span>
          <span aria-hidden="true">⌄</span>
        </summary>
        <div className="account-popover">
          <p>{auth.user?.email}</p>
          <Link to="/setup">Edit your profile & preferences</Link>
          <button onClick={logout} disabled={busy}>
            {busy ? "Signing out…" : "Sign out"}
          </button>
          {error && (
            <p className="error-message" role="alert">
              {error}
            </p>
          )}
        </div>
      </details>
    </header>
  );
}
