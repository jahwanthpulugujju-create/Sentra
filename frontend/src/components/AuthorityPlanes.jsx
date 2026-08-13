import React from "react";
import { COLORS } from "../theme";

const PLANES = [
  {
    title: "1. Control Plane",
    subtitle: "Deterministic Policy Kernel",
    badge: "Policy Engine",
    color: "#0284c7",
    items: [
      "Fixed schema & parameter validation",
      "Key-sorted canonical JSON SHA-256 hash",
      "Fail-closed rules (ALLOW / DENY / ESCALATE / FREEZE)",
      "Strict policy versioning (v1.0.0-sentra-kernel)",
    ],
  },
  {
    title: "2. Enforcement Plane",
    subtitle: "Independent Execution Gateway",
    badge: "Gateway Boundary",
    color: "#881337",
    items: [
      "Only path allowed to touch protected resources",
      "HMAC-SHA256 signature verification",
      "Atomic capability status consumption",
      "Replay & expired capability defense",
    ],
  },
  {
    title: "3. Data Plane",
    subtitle: "Protected Software State",
    badge: "State Modification",
    color: "#15803d",
    items: [
      "Isolated protected resources ledger",
      "State mutates only after gateway ALLOW",
      "Single-execution constraint per capability",
      "Deterministic initial demo baseline",
    ],
  },
  {
    title: "4. Evidence Plane",
    subtitle: "Immutable Proof Chain",
    badge: "Hash-Linked Ledger",
    color: "#b45309",
    items: [
      "Monotonic sequence numbers",
      "eventHash = SHA256(prevHash + payload)",
      "Instant automated tamper detection",
      "Read-only event replay reconstruction",
    ],
  },
];

export default function AuthorityPlanes() {
  return (
    <div
      className="rounded-xl border p-6 shadow-sm mb-6"
      style={{ background: COLORS.card, borderColor: COLORS.border }}
    >
      <div className="mb-4 pb-3 border-b" style={{ borderColor: COLORS.line }}>
        <h2 className="text-lg font-bold" style={{ color: COLORS.ink }}>
          The Four Sentra Authority Planes
        </h2>
        <p className="text-xs" style={{ color: COLORS.muted }}>
          Policy, capability, gateway, and proof are distinct architectural responsibilities.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {PLANES.map((plane) => (
          <div
            key={plane.title}
            className="p-4 rounded-lg border flex flex-col justify-between"
            style={{ background: COLORS.surface, borderColor: COLORS.border }}
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="font-bold text-sm" style={{ color: COLORS.ink }}>
                  {plane.title}
                </span>
                <span
                  className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded text-white"
                  style={{ background: plane.color }}
                >
                  {plane.badge}
                </span>
              </div>
              <div className="text-xs font-medium text-slate-600 mb-3">
                {plane.subtitle}
              </div>
              <ul className="space-y-1.5 text-xs text-slate-700">
                {plane.items.map((it, idx) => (
                  <li key={idx} className="flex items-start">
                    <span className="mr-1.5 text-sky-600 font-bold">•</span>
                    <span>{it}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
