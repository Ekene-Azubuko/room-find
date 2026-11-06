import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { ApiError, type User } from "./client";
import { useApi } from "./ApiContext";

type Auth = {
  user: User | null;
  loading: boolean;
  error: string;
  setUser: (user: User | null) => void;
  reload: () => Promise<void>;
};
const AuthContext = createContext<Auth | null>(null);

/** Restore the HttpOnly session while keeping credentials out of browser storage. */
export function AuthProvider({ children }: { children: ReactNode }) {
  const api = useApi();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  /** Refresh identity and distinguish a signed-out browser from a failed connection. */
  async function reload() {
    setLoading(true);
    setError("");
    try {
      setUser((await api.me()).user);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) setUser(null);
      else
        setError(
          error instanceof Error
            ? error.message
            : "Unable to restore your session.",
        );
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    void reload();
  }, [api]);
  return (
    <AuthContext.Provider value={{ user, setUser, loading, error, reload }}>
      {children}
    </AuthContext.Provider>
  );
}

/** Read or update the authenticated identity. */
export function useAuth() {
  const auth = useContext(AuthContext);
  if (!auth) throw new Error("useAuth must be used inside AuthProvider.");
  return auth;
}
