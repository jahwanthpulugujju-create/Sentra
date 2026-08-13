import React from "react";
import { COLORS } from "../theme";

const SCENARIOS = [
  {
    id: "valid_action",
    title: "1. Valid Action",
    expected: "ALLOW",
    expectedBadgeBg: COLORS.greenLight,
    expectedTextColor: COLORS.green,
    description: "Normal ops agent deployment to production cluster.",
    proves: "Normal path is useful, not only restrictive.",
  },
  {
    id: "unauthorized_tool",
    title: "2. Unauthorized Tool",
    expected: "DENY",
    expectedBadgeBg: COLORS.oxbloodLight,
    expectedTextColor: COLORS.oxblood,
    description: "Agent attempts to call unpermitted 'delete_database' tool.",
    proves: "Agent cannot invoke tools outside granted scope.",
  },
  {
    id: "prompt_injection",
    title: "3. Prompt Injection",
    expected: "ESCALATE",
    expectedBadgeBg: COLORS.amberLight,
    expectedTextColor: COLORS.amber,
    description: "Instruction includes prompt context override attack.",
    proves: "Untrusted or ambiguous instructions do not become authority.",
  },
  {
    id: "changed_request",
    title: "4. Changed Request",
    expected: "DENY",
    expectedBadgeBg: COLORS.oxbloodLight,
    expectedTextColor: COLORS.oxblood,
    description: "Payload altered between approval and gateway verification.",
    proves: "Approval of one request cannot be reused for a changed request.",
  },
  {
    id: "burst_anomaly",
    title: "5. Burst Anomaly",
    expected: "FREEZE",
    expectedBadgeBg: COLORS.amberLight,
    expectedTextColor: COLORS.amber,
    description: "Suspicious high-frequency repeated request pattern.",
    proves: "Suspicious activity creates a safety boundary.",
  },
  {
    id: "replay_attempt",
    title: "6. Replay Attempt",
    expected: "DENY",
    expectedBadgeBg: COLORS.oxbloodLight,
    expectedTextColor: COLORS.oxblood,
    description: "Attempting to reuse an already consumed capability.",
    proves: "Consumed capability cannot cause a second side effect.",
  },
];

export default function ScenarioRunner({ onRunScenario, runningId, activeScenarioId }) {
  return (
    <div
      className="rounded-xl border p-6 shadow-sm mb-6"
      style={{ background: COLORS.card, borderColor: COLORS.border }}
    >
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold" style={{ color: COLORS.ink }}>
            Live Authority Boundary Test
          </h2>
          <p className="text-xs" style={{ color: COLORS.muted }}>
            Run the 6 mandatory scenarios through the real backend policy & gateway.
          </p>
        </div>
        <span className="text-xs font-mono px-2.5 py-1 rounded-md border" style={{ background: COLORS.surface, borderColor: COLORS.border, color: COLORS.accentBlue }}>
          6 Fixtures Ready
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {SCENARIOS.map((s) => {
          const isLoading = runningId === s.id;
          const isActive = activeScenarioId === s.id;

          return (
            <div
              key={s.id}
              onClick={() => !runningId && onRunScenario(s.id)}
              className={`p-4 rounded-lg border text-left cursor-pointer transition hover:border-slate-400 ${
                isActive ? "ring-2 ring-sky-500" : ""
              }`}
              style={{
                background: isActive ? COLORS.surface : COLORS.surfaceAlt,
                borderColor: isActive ? COLORS.accentBlue : COLORS.border,
              }}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-bold text-sm" style={{ color: COLORS.ink }}>
                  {s.title}
                </span>
                <span
                  className="text-[11px] font-mono px-2 py-0.5 rounded font-semibold border"
                  style={{
                    background: s.expectedBadgeBg,
                    color: s.expectedTextColor,
                    borderColor: s.expectedTextColor + "40",
                  }}
                >
                  {s.expected}
                </span>
              </div>
              <p className="text-xs mb-2" style={{ color: COLORS.muted }}>
                {s.description}
              </p>
              <div className="text-[10px] italic border-t pt-2 mt-2" style={{ color: COLORS.faint, borderColor: COLORS.line }}>
                Proves: {s.proves}
              </div>

              <button
                disabled={Boolean(runningId)}
                className="mt-3 w-full py-1.5 px-3 rounded text-xs font-semibold shadow-sm transition"
                style={{
                  background: COLORS.navyHeader,
                  color: "#ffffff",
                }}
              >
                {isLoading ? "Executing..." : "Run Scenario"}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
