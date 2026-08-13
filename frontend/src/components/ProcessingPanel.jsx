import { useEffect, useState } from "react";
import { COLORS, DECISION_COLOR } from "../theme";

// Chip color from each check's result in the `checks` blob.
function ruleState(c) {
  if (!c) return "idle";
  return c.passed ? "pass" : "fail";
}
function intentState(c) {
  if (!c || !c.ran) return "idle";
  return c.match ? "pass" : "warn";
}
function anomalyState(c) {
  if (!c || !c.ran) return "idle";
  return c.flagged ? "warn" : "pass";
}

const STATE_COLOR = {
  idle: COLORS.faint,
  pass: COLORS.green,
  warn: COLORS.amber,
  fail: COLORS.red,
  checking: COLORS.amber,
};

const LLM_AUTHORITY_LABELS = {
  not_consulted: "LLM not consulted — hard rule violation",
  advisory_only: "LLM verdict: advisory only — final decision by policy engine",
  fallback_used: "LLM unavailable — keyword heuristic used as fallback",
};

function Chip({ label, state, revealed, checking }) {
  const color = checking ? STATE_COLOR.checking : STATE_COLOR[state] || COLORS.faint;
  return (
    <div
      className="flex items-center gap-2 px-3 py-2 rounded-lg border transition-all"
      style={{
        borderColor: COLORS.line,
        background: COLORS.panelAlt,
        opacity: revealed ? 1 : 0.35,
      }}
    >
      <span
        className="inline-block w-2 h-2 rounded-full"
        style={{
          background: color,
          animation: checking ? "pulse 1s infinite" : "none",
        }}
      />
      <span className="text-sm" style={{ color: COLORS.ink }}>
        {label}
      </span>
    </div>
  );
}

function RiskMeter({ score }) {
  const riskColor =
    score >= 70 ? COLORS.red : score >= 40 ? COLORS.amber : COLORS.green;
  const label =
    score >= 70 ? "HIGH" : score >= 40 ? "MEDIUM" : "LOW";

  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: COLORS.panelAlt }}>
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${Math.min(score, 100)}%`, background: riskColor }}
        />
      </div>
      <span className="text-xs font-mono font-semibold" style={{ color: riskColor }}>
        {score.toFixed(0)} · {label}
      </span>
    </div>
  );
}

export default function ProcessingPanel({ running, result }) {
  const [stage, setStage] = useState(3); // how many chips are revealed

  useEffect(() => {
    if (running) {
      setStage(0);
      const t1 = setTimeout(() => setStage(1), 250);
      const t2 = setTimeout(() => setStage(2), 600);
      const t3 = setTimeout(() => setStage(3), 950);
      return () => {
        clearTimeout(t1);
        clearTimeout(t2);
        clearTimeout(t3);
      };
    }
    setStage(3);
  }, [running, result]);

  const checks = result && result.checks ? result.checks : null;
  const chips = [
    { label: "Rule engine", state: ruleState(checks && checks.rule_engine) },
    { label: "Intent match", state: intentState(checks && checks.intent_match) },
    { label: "Anomaly score", state: anomalyState(checks && checks.anomaly) },
  ];

  const showBanner = !running && result;
  const bannerColor = result ? DECISION_COLOR[result.decision] || COLORS.muted : COLORS.muted;

  const intent = checks && checks.intent_match;
  const anomaly = checks && checks.anomaly;
  const riskScore = result?.risk_score;
  const riskFactors = result?.risk_factors || [];
  const llmAuthority = result?.llm_authority;
  const processingTime = result?.processing_time_ms;

  return (
    <section
      className="rounded-xl p-4 border backdrop-blur-md shadow-glass"
      style={{ background: COLORS.panel, borderColor: COLORS.line }}
    >
      <style>{`@keyframes pulse{0%{opacity:1}50%{opacity:.3}100%{opacity:1}}`}</style>
      <div
        className="text-xs uppercase tracking-wider mb-3"
        style={{ color: COLORS.faint }}
      >
        Sentra Policy Engine
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
        {chips.map((c, i) => (
          <Chip
            key={c.label}
            label={c.label}
            state={c.state}
            revealed={stage > i}
            checking={running && stage > i}
          />
        ))}
      </div>

      {showBanner && (
        <div className="mt-4">
          <div
            className="px-3 py-2 rounded-lg border font-semibold uppercase tracking-wide"
            style={{ borderColor: bannerColor, color: bannerColor }}
          >
            {result.decision}
          </div>
          <div className="mt-2 text-sm" style={{ color: COLORS.ink }}>
            {result.reason}
          </div>

          {/* Risk Score Meter */}
          {riskScore != null && (
            <div className="mt-3">
              <div className="text-xs uppercase tracking-wider mb-1" style={{ color: COLORS.faint }}>
                Risk Score
              </div>
              <RiskMeter score={riskScore} />
            </div>
          )}

          {/* Risk Factors */}
          {riskFactors.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {riskFactors.map((f, i) => (
                <span
                  key={i}
                  className="text-xs px-2 py-0.5 rounded-full border"
                  style={{
                    borderColor: COLORS.red + "40",
                    color: COLORS.red,
                    background: COLORS.red + "10",
                  }}
                >
                  {f}
                </span>
              ))}
            </div>
          )}

          {checks && (
            <div
              className="mt-3 text-xs space-y-1 font-mono"
              style={{ color: COLORS.muted }}
            >
              {intent && intent.ran && (
                <div>
                  intent: {String(intent.match)} · source {intent.source}
                  {intent.confidence != null && ` · confidence ${(intent.confidence * 100).toFixed(0)}%`}
                  {intent.injection_detected && (
                    <span style={{ color: COLORS.red }}> · ⚠ injection detected</span>
                  )}
                </div>
              )}
              {anomaly && anomaly.ran && anomaly.z_score != null && (
                <div>
                  anomaly: flagged {String(anomaly.flagged)} · z=
                  {Number(anomaly.z_score).toFixed(1)} · mean ₹
                  {Math.round(anomaly.mean)}
                </div>
              )}
              {processingTime != null && (
                <div>processed in {processingTime.toFixed(0)}ms</div>
              )}
            </div>
          )}

          {/* LLM Authority Boundary */}
          {llmAuthority && (
            <div
              className="mt-2 text-xs px-2 py-1 rounded border"
              style={{
                borderColor: COLORS.line,
                color: COLORS.faint,
                background: COLORS.panelAlt,
              }}
            >
              🔒 {LLM_AUTHORITY_LABELS[llmAuthority] || llmAuthority}
            </div>
          )}
        </div>
      )}

      {!showBanner && !running && (
        <div className="mt-4 text-sm" style={{ color: COLORS.faint }}>
          Submit a transaction to see the engine decide.
        </div>
      )}
    </section>
  );
}
