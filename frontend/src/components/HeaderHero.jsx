import React from "react";
import { COLORS } from "../theme";

export default function HeaderHero({ health, onReset, resetting }) {
  return (
    <div
      className="rounded-xl border p-6 shadow-sm mb-6"
      style={{
        background: `linear-gradient(135deg, ${COLORS.card} 0%, ${COLORS.surface} 100%)`,
        borderColor: COLORS.border,
      }}
    >
      {/* Top bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b" style={{ borderColor: COLORS.line }}>
        <div className="flex items-center space-x-3">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center font-bold text-white shadow-sm"
            style={{ background: COLORS.navyHeader }}
          >
            S
          </div>
          <div>
            <span className="font-bold text-lg tracking-tight" style={{ color: COLORS.ink }}>
              SENTRA
            </span>
            <span className="ml-2 text-xs px-2 py-0.5 rounded font-mono border" style={{ background: COLORS.surfaceAlt, color: COLORS.muted, borderColor: COLORS.border }}>
              v2.0 Authority Engine
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-xs font-medium" style={{ color: COLORS.muted }}>
            <span className={`w-2.5 h-2.5 rounded-full ${health?.db_connected ? "bg-emerald-600" : "bg-rose-600"}`} />
            <span>{health?.db_connected ? "Engine Ready" : "Connecting..."}</span>
          </div>
          <button
            onClick={onReset}
            disabled={resetting}
            className="px-3 py-1.5 text-xs font-semibold rounded-md border transition hover:bg-slate-100"
            style={{ borderColor: COLORS.border, color: COLORS.ink, background: COLORS.card }}
          >
            {resetting ? "Resetting..." : "Reset Baseline State"}
          </button>
        </div>
      </div>

      {/* Main Hero Headline */}
      <div className="mt-6 mb-6">
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight" style={{ color: COLORS.ink }}>
          Every agent action needs a real yes.
        </h1>
        <p className="mt-2 text-base sm:text-lg max-w-3xl" style={{ color: COLORS.muted }}>
          <strong style={{ color: COLORS.oxblood }}>“An agent can propose an action. Sentra decides whether it has authority to execute it.”</strong>
        </p>
      </div>

      {/* Hero Pipeline Visualizer Artifact */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-2 text-xs font-mono">
        <div className="p-3 rounded-lg border text-center" style={{ background: COLORS.card, borderColor: COLORS.border }}>
          <div className="font-semibold text-slate-500 mb-1">1. AGENT PROPOSAL</div>
          <div className="font-bold text-slate-800">Canonical Request</div>
          <div className="text-[10px] text-slate-500 mt-1">SHA-256 Hash Binding</div>
        </div>
        <div className="p-3 rounded-lg border text-center" style={{ background: COLORS.surfaceAlt, borderColor: COLORS.border }}>
          <div className="font-semibold text-slate-500 mb-1">2. POLICY KERNEL</div>
          <div className="font-bold text-slate-800">Deterministic Rules</div>
          <div className="text-[10px] text-slate-500 mt-1">v1.0.0 Fail-Closed</div>
        </div>
        <div className="p-3 rounded-lg border text-center" style={{ background: COLORS.card, borderColor: COLORS.border }}>
          <div className="font-semibold text-slate-500 mb-1">3. CAPABILITY</div>
          <div className="font-bold text-slate-800">HMAC-SHA256 Signed</div>
          <div className="text-[10px] text-slate-500 mt-1">Short TTL & Nonce</div>
        </div>
        <div className="p-3 rounded-lg border text-center" style={{ background: COLORS.surfaceAlt, borderColor: COLORS.border }}>
          <div className="font-semibold text-slate-500 mb-1">4. GATEWAY</div>
          <div className="font-bold text-slate-800">Independent Verifier</div>
          <div className="text-[10px] text-slate-500 mt-1">Atomic Consumption</div>
        </div>
        <div className="p-3 rounded-lg border text-center" style={{ background: COLORS.card, borderColor: COLORS.border }}>
          <div className="font-semibold text-slate-500 mb-1">5. PROOF CHAIN</div>
          <div className="font-bold text-slate-800">Immutable Audit</div>
          <div className="text-[10px] text-slate-500 mt-1">Hash-Linked Ledger</div>
        </div>
      </div>
    </div>
  );
}
