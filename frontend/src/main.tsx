import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import type { ReactNode } from "react";
import { ApiProvider } from "./api/ApiContext";
import { AuthProvider, useAuth } from "./api/AuthContext";
import { Landing } from "./pages/Landing";
import { AuthPage } from "./pages/AuthPage";
import { Setup } from "./pages/Setup";
import { Home } from "./pages/Home";
import { Header } from "./components/Header";
import "@fontsource/inter/latin-400.css";
import "@fontsource/inter/latin-500.css";
import "@fontsource/inter/latin-600.css";
import "@fontsource/inter/latin-700.css";
import "./styles.css";
import "./discovery.css";

/** Wait for session restoration before rendering a private route. */
function Protected({ children }: { children: ReactNode }) {
  const auth = useAuth();
  if (auth.loading)
    return (
      <>
        <Header />
        <main className="status-page" role="status">
          Making you feel at home…
        </main>
      </>
    );
  if (auth.error)
    return (
      <>
        <Header />
        <main className="status-page">
          <p role="alert">{auth.error}</p>
          <button className="button primary" onClick={auth.reload}>
            Try again
          </button>
        </main>
      </>
    );
  return auth.user ? children : <Navigate to="/login" replace />;
}

createRoot(document.getElementById("root")!).render(
  <BrowserRouter>
    <ApiProvider>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route
            path="/register"
            element={<AuthPage key="register" register />}
          />
          <Route path="/login" element={<AuthPage key="login" />} />
          <Route
            path="/setup"
            element={
              <Protected>
                <Setup />
              </Protected>
            }
          />
          <Route
            path="/app"
            element={
              <Protected>
                <Home />
              </Protected>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </ApiProvider>
  </BrowserRouter>,
);
