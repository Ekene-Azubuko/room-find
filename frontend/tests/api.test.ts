import { afterEach, mock, test } from "node:test";
import assert from "node:assert/strict";
import { ApiError, createApiClient } from "../src/api/client.ts";

afterEach(() => mock.restoreAll());

/** Capture requests and return a sequence of server responses without a live database. */
function fakeServer(responses: Response[]) {
  const calls: { url: string; options?: RequestInit }[] = [];
  mock.method(
    globalThis,
    "fetch",
    async (url: string, options?: RequestInit) => {
      calls.push({ url, options });
      const response = responses.shift();
      assert.ok(response, `Unexpected request: ${url}`);
      return response;
    },
  );
  return calls;
}

test("writes use cookies and a new CSRF token after the login session rotates", async () => {
  const calls = fakeServer([
    Response.json({ csrf_token: "before-login" }),
    Response.json({ user: { id: 1, email: "sam@example.test" } }),
    Response.json({ csrf_token: "after-login" }),
    Response.json({ message: "Logged out." }),
  ]);
  const api = createApiClient();
  await api.login({ email: "sam@example.test", password: "test-password" });
  await api.logout();
  assert.deepEqual(
    calls.map((call) => call.url),
    ["/api/auth/csrf", "/api/auth/login", "/api/auth/csrf", "/api/auth/logout"],
  );
  assert.equal(
    (calls[1].options?.headers as Record<string, string>)["X-CSRF-Token"],
    "before-login",
  );
  assert.equal(
    (calls[3].options?.headers as Record<string, string>)["X-CSRF-Token"],
    "after-login",
  );
  assert.ok(calls.every((call) => call.options?.credentials === "same-origin"));
});

test("duplicate accounts retain the server message and status", async () => {
  fakeServer([
    Response.json({ csrf_token: "token" }),
    Response.json(
      { error: "An account with this email already exists." },
      { status: 409 },
    ),
  ]);
  await assert.rejects(
    createApiClient().register({
      email: "sam@example.test",
      password: "test-password",
    }),
    {
      name: "Error",
      message: "An account with this email already exists.",
      status: 409,
    },
  );
});

test("an expired session stays distinguishable from a failed connection", async () => {
  fakeServer([
    Response.json({ error: "Authentication required." }, { status: 401 }),
  ]);
  await assert.rejects(
    createApiClient().me(),
    (error: unknown) => error instanceof ApiError && error.status === 401,
  );
  mock.restoreAll();
  mock.method(globalThis, "fetch", async () => {
    throw new TypeError("Failed to fetch");
  });
  await assert.rejects(
    createApiClient().me(),
    (error: unknown) =>
      error instanceof ApiError &&
      error.status === 0 &&
      error.message.includes("Unable to connect"),
  );
});

test("photo uploads leave the multipart boundary to the browser", async () => {
  const calls = fakeServer([
    Response.json({ csrf_token: "token" }),
    Response.json({ profile: { photo_url: "/api/profile/photo" } }),
  ]);
  await createApiClient().uploadPhoto(
    new File(["sample"], "photo.png", { type: "image/png" }),
  );
  assert.ok(calls[1].options?.body instanceof FormData);
  assert.equal(
    (calls[1].options?.headers as Record<string, string>)["Content-Type"],
    undefined,
  );
  assert.equal(
    (calls[1].options?.headers as Record<string, string>)["X-CSRF-Token"],
    "token",
  );
});

test("an HTML proxy failure produces a readable error", async () => {
  fakeServer([new Response("<h1>Bad gateway</h1>", { status: 502 })]);
  await assert.rejects(createApiClient().me(), {
    message: "The server is unavailable. Please try again.",
    status: 502,
  });
});
