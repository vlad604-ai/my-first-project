/** Typed API client shared by the Mini App and the admin dashboard. */
const BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ?? "";

function storageGet(key: string): string | null {
  try { return localStorage.getItem(key); } catch { return null; }
}
function storageSet(key: string, value: string | null) {
  try { value === null ? localStorage.removeItem(key) : localStorage.setItem(key, value); } catch { /* ignore */ }
}

export class ApiError extends Error {
  constructor(public status: number, public detail: unknown) {
    super(typeof detail === "string" ? detail : (detail as { message?: string })?.message ?? `HTTP ${status}`);
  }
}

export function createClient(tokenKey: string) {
  let token: string | null = storageGet(tokenKey);
  async function request<T>(method: string, path: string, body?: unknown, params?: Record<string, unknown>): Promise<T> {
    const url = new URL(`${BASE}/api/v1${path}`, window.location.origin);
    Object.entries(params ?? {}).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, String(v));
    });
    const res = await fetch(url.toString(), {
      method,
      headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (res.status === 204) return undefined as T;
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new ApiError(res.status, (data as { detail?: unknown }).detail ?? data);
    return data as T;
  }
  return {
    get token() { return token; },
    setToken(value: string | null) { token = value; storageSet(tokenKey, value); },
    get: <T,>(path: string, params?: Record<string, unknown>) => request<T>("GET", path, undefined, params),
    post: <T,>(path: string, body?: unknown, params?: Record<string, unknown>) => request<T>("POST", path, body, params),
    put: <T,>(path: string, body?: unknown) => request<T>("PUT", path, body),
    del: <T,>(path: string) => request<T>("DELETE", path),
  };
}

export const euro = (cents: number | null | undefined) =>
  cents === null || cents === undefined ? "Sur devis"
    : new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: cents % 100 ? 2 : 0 }).format(cents / 100);

export const fmtDateTime = (iso: string) =>
  new Intl.DateTimeFormat("fr-FR", { weekday: "long", day: "numeric", month: "long", hour: "2-digit", minute: "2-digit", timeZone: "Europe/Paris" }).format(new Date(iso));

export const fmtTime = (iso: string) =>
  new Intl.DateTimeFormat("fr-FR", { hour: "2-digit", minute: "2-digit", timeZone: "Europe/Paris" }).format(new Date(iso));

export const parisDay = (iso: string) =>
  new Intl.DateTimeFormat("fr-CA", { timeZone: "Europe/Paris" }).format(new Date(iso)); // YYYY-MM-DD
