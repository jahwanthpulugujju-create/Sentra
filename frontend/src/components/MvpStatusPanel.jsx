import React from "react";
import { COLORS } from "../theme";

export default function MvpStatusPanel() {
  return (
    <div className="space-y-6">
      {/* MVP Scope & Honest Limitations */}
      <div
        className="rounded-xl border p-6 shadow-sm"
        style={{ background: COLORS.card, borderColor: COLORS.border }}
      >
        <div className="mb-4 pb-3 border-b" style={{ borderColor: COLORS.line }}>
          <h2 className="text-lg font-bold" style={{ color: COLORS.ink }}>
            MVP Scope & Engineering Discipline
          </h2>
          <p className="text-xs" style={{ color: COLORS.muted }}>
            Honest boundaries: Sentra implements one authority boundary with precision instead of an oversized dashboard.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          {/* Completed Scope */}
          <div className="p-3.5 rounded-lg border bg-emerald-50/60 border-emerald-200">
            <div className="font-bold text-emerald-900 mb-2 flex items-center">
              <span className="w-2 h-2 rounded-full bg-emerald-600 mr-2" />
              Completed Core MVP
            </div>
            <ul className="space-y-1 text-emerald-800">
              <li>✓ Single protected tool boundary</li>
              <li>✓ Key-sorted canonical request SHA-256</li>
              <li>✓ Deterministic policy fail-closed kernel</li>
              <li>✓ HMAC-SHA256 capability issuance</li>
              <li>✓ Independent Gateway verification</li>
              <li>✓ Hash-linked proof chain ledger</li>
            </ul>
          </div>

          {/* Intentionally Excluded */}
          <div className="p-3.5 rounded-lg border bg-slate-50 border-slate-200">
            <div className="font-bold text-slate-800 mb-2 flex items-center">
              <span className="w-2 h-2 rounded-full bg-slate-500 mr-2" />
              Intentionally Excluded
            </div>
            <ul className="space-y-1 text-slate-700">
              <li>✕ Multi-tool governance marketplace</li>
              <li>✕ LLM chat interface</li>
              <li>✕ Real-time collaboration rooms</li>
              <li>✕ Third-party payment gateways</li>
              <li>✕ Large custom policy language parser</li>
            </ul>
          </div>

          {/* Known Limitations */}
          <div className="p-3.5 rounded-lg border bg-amber-50/60 border-amber-200">
            <div className="font-bold text-amber-900 mb-2 flex items-center">
              <span className="w-2 h-2 rounded-full bg-amber-600 mr-2" />
              Known Hackathon Limitations
            </div>
            <ul className="space-y-1 text-amber-800">
              <li>• Fixed signing key (HMAC-SHA256)</li>
              <li>• Single resource fixture focus</li>
              <li>• Local SQLite / PostgreSQL storage</li>
              <li>• Pre-configured agent identity scopes</li>
            </ul>
          </div>

          {/* Test Evidence */}
          <div className="p-3.5 rounded-lg border bg-sky-50/60 border-sky-200">
            <div className="font-bold text-sky-900 mb-2 flex items-center">
              <span className="w-2 h-2 rounded-full bg-sky-600 mr-2" />
              Automated Test Suite
            </div>
            <ul className="space-y-1 text-sky-800">
              <li>✓ 10 Automated test suites passing</li>
              <li>✓ Canonicalization hash stability</li>
              <li>✓ Replay rejection verification</li>
              <li>✓ Changed-request hash refusal</li>
              <li>✓ Proof chain tamper detection</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Closing Sentence Banner */}
      <div
        className="rounded-xl border p-6 text-center shadow-md"
        style={{
          background: COLORS.navyHeader,
          borderColor: COLORS.border,
          color: "#ffffff",
        }}
      >
        <p className="text-xl sm:text-2xl font-extrabold tracking-tight">
          “The model can change its reasoning. It cannot change its authority.”
        </p>
        <p className="text-xs text-slate-400 mt-2 font-mono">
          Sentra Authority Engine • 2026 Winner-Readiness Playbook
        </p>
      </div>
    </div>
  );
}
