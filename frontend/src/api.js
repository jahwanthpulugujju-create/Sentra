// Thin fetch wrappers for every backend endpoint (BUILD_PLAN.md §8).
// No business logic here — the backend owns all decisions.
const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function req(path, opts) {
  const res = await fetch(BASE + path, opts);
  if (!res.ok) {
    let detail = "";
    try {
      detail = (await res.json()).detail || "";
    } catch {
      /* ignore */
    }
    throw new Error(`${res.status} ${res.statusText}${detail ? ` — ${detail}` : ""}`);
  }
  return res.status === 204 ? null : res.json();
}

const jsonPost = (path, body) =>
  req(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

export const getHealth = () => req("/health");
export const getAgents = () => req("/agents");
export const getTransactions = (limit = 50) => req(`/transactions?limit=${limit}`);
export const evaluate = (body) => jsonPost("/evaluate-transaction", body);
export const reset = () => req("/reset", { method: "POST" });

// Defined for M4 (escalation resolve) — the route is not built until M4.
export const resolve = (body) => jsonPost("/resolve-escalation", body);
export const getMetrics = () => req("/metrics");
