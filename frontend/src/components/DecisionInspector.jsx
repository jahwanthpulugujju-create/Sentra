import React, { useState } from "react";
import { COLORS, VERDICT_COLOR } from "../theme";

export default function DecisionInspector({ lastResult, resourceState }) {
  const [showRawJson, setShowRawJson] = useState(false);

  if (!lastResult) {
    return (
      <div
        className="rounded-xl border p-6 shadow-sm mb-6 text-center"
        style={{ background: COLORS.card, borderColor: COLORS.border }}
      >
        <h3 className="font-bold text-base mb-1" style={{ color: COLORS.ink }}>
          Decision Inspector
        </h3>
        <p className="text-xs" style={{ color: COLORS.muted }}>
          Select a scenario above to inspect canonical request, request hash, policy decision, signed capability, and gateway execution.
        </p>
      </div>
    );
  }

  const verdict = lastResult.verdict || "DENY";
  const verdictTheme = VERDICT_COLOR[verdict] || VERDICT_COLOR.DENY;

  return (
    <div
      className="rounded-xl border p-6 shadow-sm mb-6"
      style={{ background: COLORS.card, borderColor: COLORS.border }}
    >
      <div className="flex flex-wrap items-center justify-between gap-2 mb-4 pb-3 border-b" style={{ borderColor: COLORS.line }}>
        <div className="flex items-center space-x-2">
          <h2 className="text-lg font-bold" style={{ color: COLORS.ink }}>
            Decision Inspector
          </h2>
          <span className="text-xs font-mono px-2 py-0.5 rounded border" style={{ background: COLORS.surface, color: COLORS.muted, borderColor: COLORS.border }}>
            Scenario: {lastResult.scenario || "Custom"}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowRawJson(!showRawJson)}
            className="text-xs font-mono px-2.5 py-1 rounded border hover:bg-slate-100"
            style={{ background: COLORS.surfaceAlt, color: COLORS.ink, borderColor: COLORS.border }}
          >
            {showRawJson ? "Hide Raw Payload" : "View Raw JSON"}
          </button>
          <span
            className="text-xs font-mono px-3 py-1 rounded-md font-bold border"
            style={{
              background: verdictTheme.bg,
              color: verdictTheme.text,
              borderColor: verdictTheme.border,
            }}
          >
            VERDICT: {verdict}
          </span>
        </div>
      </div>

      {showRawJson ? (
        <pre className="p-4 rounded-lg bg-slate-900 text-emerald-400 font-mono text-xs overflow-x-auto mb-4">
          {JSON.stringify(lastResult, null, 2)}
        </pre>
      ) : null}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Left Column: Request & Policy Decision */}
        <div className="space-y-4">
          {/* 1. Request Hash & Canonicalization */}
          <div className="p-4 rounded-lg border" style={{ background: COLORS.surface, borderColor: COLORS.border }}>
            <div className="text-xs font-bold uppercase tracking-wider mb-2" style={{ color: COLORS.faint }}>
              1. Canonical Request & SHA-256 Hash
            </div>
            <div className="mb-2">
              <span className="text-[11px] font-mono text-slate-500">requestHash:</span>
              <div className="font-mono text-xs font-bold p-2 rounded border bg-white break-all mt-1" style={{ borderColor: COLORS.border, color: COLORS.ink }}>
                {lastResult.requestHash || "N/A"}
              </div>
            </div>

            {lastResult.tamperedHash && (
              <div className="mb-2">
                <span className="text-[11px] font-mono text-rose-600 font-bold">Tampered Gateway Hash (Mismatch!):</span>
                <div className="font-mono text-xs font-bold p-2 rounded border bg-rose-50 text-rose-900 break-all mt-1" style={{ borderColor: "#fecdd3" }}>
                  {lastResult.tamperedHash}
                </div>
              </div>
            )}
          </div>

          {/* 2. Deterministic Policy Kernel Verdict */}
          <div className="p-4 rounded-lg border" style={{ background: COLORS.card, borderColor: COLORS.border }}>
            <div className="text-xs font-bold uppercase tracking-wider mb-2" style={{ color: COLORS.faint }}>
              2. Deterministic Policy Kernel Verdict
            </div>
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-xs font-semibold" style={{ color: COLORS.muted }}>Reason Code:</span>
              <span className="font-mono text-xs font-bold px-2 py-0.5 rounded border" style={{ background: COLORS.surfaceAlt, borderColor: COLORS.border, color: COLORS.ink }}>
                {lastResult.reasonCode}
              </span>
            </div>
            <p className="text-xs p-2.5 rounded border" style={{ background: COLORS.surface, borderColor: COLORS.border, color: COLORS.ink }}>
              {lastResult.explanation}
            </p>
          </div>
        </div>

        {/* Right Column: Capability & Gateway Execution */}
        <div className="space-y-4">
          {/* 3. Cryptographically Signed Capability */}
          <div className="p-4 rounded-lg border" style={{ background: COLORS.card, borderColor: COLORS.border }}>
            <div className="text-xs font-bold uppercase tracking-wider mb-2" style={{ color: COLORS.faint }}>
              3. Signed Capability (HMAC-SHA256)
            </div>
            {lastResult.capability ? (
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-500 font-mono">capabilityId:</span>
                  <span className="font-mono font-bold" style={{ color: COLORS.accentBlue }}>
                    {lastResult.capability.id}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-mono">status:</span>
                  <span className="font-mono font-bold text-emerald-700">
                    {lastResult.capability.status}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 font-mono text-[11px]">HMAC Signature:</span>
                  <div className="font-mono text-[11px] p-1.5 rounded bg-slate-50 border break-all text-slate-700 mt-1" style={{ borderColor: COLORS.border }}>
                    {lastResult.capability.signature}
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-3 rounded bg-rose-50 text-rose-900 border text-xs" style={{ borderColor: "#fecdd3" }}>
                <strong>No Capability Issued:</strong> Policy verdict was {verdict}. State modification is blocked before reaching gateway.
              </div>
            )}
          </div>

          {/* 4. Independent Gateway Execution & State Change */}
          <div className="p-4 rounded-lg border" style={{ background: COLORS.surface, borderColor: COLORS.border }}>
            <div className="text-xs font-bold uppercase tracking-wider mb-2" style={{ color: COLORS.faint }}>
              4. Gateway Verification & Resource State
            </div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-slate-600 font-medium">State Mutation Status:</span>
              <span
                className={`text-xs font-bold px-2 py-0.5 rounded border ${
                  lastResult.stateChanged ? "bg-emerald-100 text-emerald-800 border-emerald-300" : "bg-rose-100 text-rose-800 border-rose-300"
                }`}
              >
                {lastResult.stateChanged ? "STATE CHANGED (1x)" : "PROTECTED STATE UNCHANGED"}
              </span>
            </div>

            {resourceState && (
              <div className="p-3 rounded bg-white border text-xs font-mono mt-2" style={{ borderColor: COLORS.border }}>
                <div className="text-slate-500 text-[10px] mb-1">Target Resource: prod_k8s_cluster</div>
                <div className="text-slate-900 font-semibold">
                  Status: {resourceState.status} | Deploy Count: {resourceState.deployCount}
                </div>
                <div className="text-slate-500 text-[11px] mt-1">
                  Last Deploy By: {resourceState.lastDeployBy} ({resourceState.lastAction || "none"})
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
