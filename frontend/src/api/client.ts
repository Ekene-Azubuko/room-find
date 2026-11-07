export type User = { id: number; email: string };
export type Credentials = { email: string; password: string };
export type Profile = User & {
  full_name: string | null;
  bio: string | null;
  age: number | null;
  life_stage: string | null;
  occupation: string | null;
  photo_url: string | null;
  onboarding_completed_at: string | null;
};
export type Housing = {
  city: string | null;
  neighborhood: string | null;
  budget_min: string | null;
  budget_max: string | null;
  move_in_date: string | null;
  lease_months: number | null;
  city_is_requirement: boolean;
  budget_is_requirement: boolean;
  neighborhood_is_requirement: boolean;
  move_in_is_requirement: boolean;
  lease_is_requirement: boolean;
};
export type Answer = {
  question_key: string;
  own_answer: string | null;
  roommate_answer: string | null;
  is_requirement: boolean;
};
export type Roommate = {
  id: number;
  full_name: string;
  age: number;
  occupation: string;
  bio: string;
  life_stage: string;
  photo_url: string;
  is_demo: boolean;
  housing: Pick<
    Housing,
    | "city"
    | "neighborhood"
    | "budget_min"
    | "budget_max"
    | "move_in_date"
    | "lease_months"
  > | null;
  lifestyle: Record<string, string | null>;
};

/** Preserve the server's HTTP status so callers can distinguish expired sessions. */
export class ApiError extends Error {
  status: number;
  /** Attach an HTTP status to a readable server or connection error. */
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

/** Create a small same-origin client with cookies and CSRF handling in one place. */
export function createApiClient() {
  /** Send JSON or multipart data and surface useful API errors. */
  async function request<T>(
    path: string,
    method = "GET",
    body?: unknown,
  ): Promise<T> {
    const headers: Record<string, string> = {};
    try {
      // Fetch per write: login/logout rotate the session and invalidate old tokens.
      if (method !== "GET") {
        const token = await request<{ csrf_token: string }>("/auth/csrf");
        headers["X-CSRF-Token"] = token.csrf_token;
      }
      const multipart = body instanceof FormData;
      if (body !== undefined && !multipart)
        headers["Content-Type"] = "application/json";
      const response = await fetch(`/api${path}`, {
        method,
        headers,
        credentials: "same-origin",
        cache: "no-store",
        body:
          body === undefined
            ? undefined
            : multipart
              ? body
              : JSON.stringify(body),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok)
        throw new ApiError(
          data?.error || "The server is unavailable. Please try again.",
          response.status,
        );
      if (data === null)
        throw new ApiError(
          "The server returned an unexpected response.",
          response.status,
        );
      return data as T;
    } catch (error) {
      if (error instanceof ApiError) throw error;
      throw new ApiError(
        "Unable to connect. Check your connection and try again.",
        0,
      );
    }
  }
  return {
    /** List seeded discovery profiles without compatibility ranking. */
    roommates: () => request<{ roommates: Roommate[] }>("/roommates"),
    /** Read a demo roommate by ID; private accounts are never exposed. */
    roommate: (id: string) =>
      request<{ roommate: Roommate }>(`/roommates/${encodeURIComponent(id)}`),
    /** Create credentials without implicitly changing the server session. */
    register: (credentials: Credentials) =>
      request<{ user: User }>("/auth/register", "POST", credentials),
    /** Start a cookie-backed session. */
    login: (credentials: Credentials) =>
      request<{ user: User }>("/auth/login", "POST", credentials),
    /** Restore the browser's existing session. */
    me: () => request<{ user: User }>("/auth/me"),
    /** End the browser's session. */
    logout: () => request("/auth/logout", "POST"),
    /** Read saved profile details. */
    profile: () => request<{ profile: Profile }>("/profile"),
    /** Save only editable profile fields. */
    saveProfile: (
      profile: Partial<
        Pick<Profile, "full_name" | "age" | "life_stage" | "occupation" | "bio">
      >,
    ) => request("/profile", "PATCH", profile),
    /** Upload a photo through the same protected client. */
    uploadPhoto: (photo: File) => {
      const body = new FormData();
      body.set("photo", photo);
      return request<{ profile: Profile }>("/profile/photo", "PUT", body);
    },
    /** Read the account's housing preferences. */
    housing: () => request<{ housing: Housing | null }>("/preferences/housing"),
    /** Persist a partial housing update. */
    saveHousing: (housing: Partial<Housing>) =>
      request("/preferences/housing", "PATCH", housing),
    /** Read saved lifestyle choices. */
    lifestyle: () => request<{ answers: Answer[] }>("/preferences/lifestyle"),
    /** Replace one own/roommate preference pair. */
    saveAnswer: ({ question_key, ...answer }: Answer) =>
      request(`/preferences/lifestyle/${question_key}`, "PUT", answer),
    /** Ask the backend to validate and complete the saved profile. */
    complete: () => request("/onboarding/complete", "POST"),
  };
}
export type ApiClient = ReturnType<typeof createApiClient>;
