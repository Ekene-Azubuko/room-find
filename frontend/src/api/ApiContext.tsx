import { createContext, useContext, useState, type ReactNode } from "react";
import { createApiClient, type ApiClient } from "./client";

const ApiContext = createContext<ApiClient | null>(null);

/** Provide one stable API client to the application. */
export function ApiProvider({ children }: { children: ReactNode }) {
  const [client] = useState(createApiClient);
  return <ApiContext.Provider value={client}>{children}</ApiContext.Provider>;
}

/** Access the client without coupling pages to fetch or transport details. */
export function useApi() {
  const client = useContext(ApiContext);
  if (!client) throw new Error("useApi must be used inside ApiProvider.");
  return client;
}
