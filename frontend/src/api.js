const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function req(path, opts) {
  const res = await fetch(BASE + path, opts);
  if (!res.ok) {
    let detail = "";
    try {
      const json = await res.json();
      detail = json.detail ? (typeof json.detail === "object" ? JSON.stringify(json.detail) : json.detail) : "";
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
export const getDashboard = () => req("/dashboard");
export const evaluate = (body) => jsonPost("/evaluate", body);
export const verifyAndExecute = (body) => jsonPost("/verify-and-execute", body);
export const runScenario = (scenario) => jsonPost("/run-scenario", { scenario });
export const verifyProofChain = () => req("/proof-chain/verify");
export const resetDemo = () => req("/reset-demo", { method: "POST" });
export const getReplay = (eventId) => req(`/replay/${eventId}`);
