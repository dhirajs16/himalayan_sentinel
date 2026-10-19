export const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
let accessToken = "";
export function setAccessToken(value: string) { accessToken = value; }
export function getAccessToken() { return accessToken; }
let refreshRequest: Promise<boolean> | null = null;
export async function api<T = Record<string, unknown>>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  if (init.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  let response = await fetch(`${API}/api/v1${path}`, { ...init, headers, credentials: "include", signal: init.signal || AbortSignal.timeout(25000) });
  if (response.status === 401 && accessToken && !path.startsWith("/auth/")) {
    if (!refreshRequest) refreshRequest = fetch(`${API}/api/v1/auth/refresh`, { method: "POST", credentials: "include", signal: AbortSignal.timeout(15000) }).then(async r => {
      if (!r.ok) { accessToken = ""; return false; } const result = await r.json(); accessToken = result.access_token; return true;
    }).catch(() => false).finally(() => { refreshRequest = null; });
    if (await refreshRequest) { headers.set("Authorization", `Bearer ${accessToken}`); response = await fetch(`${API}/api/v1${path}`, { ...init, headers, credentials: "include", signal: AbortSignal.timeout(25000) }); }
  }
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(typeof error.detail === "string" ? error.detail : `Request failed (${response.status}). Check the form and try again.`);
  }
  return response.json();
}
export function npt(value: string | null) {
  return value ? new Intl.DateTimeFormat("en-NP", { timeZone: "Asia/Kathmandu", dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) + " NPT" : "Not synchronized";
}
