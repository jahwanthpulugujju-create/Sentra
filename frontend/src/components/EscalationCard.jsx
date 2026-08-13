import { useState } from "react";
import { COLORS } from "../theme";
import { resolve } from "../api";

// Shown when the latest decision is an Escalate that's still `pending`
// (BUILD_PLAN.md §9). The human resolves it here.
export default function EscalationCard({ tx, request, onResolved }) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const act = async (action) => {
    setBusy(true);
    setErr(null);
    try {
      await resolve({ transaction_id: tx.transaction_id, action });
      if (onResolved) await onResolved();
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setBusy(false);
    }
  };

  const riskScore = tx.risk_score;

  return (
    <section
      className="rounded-xl p-4 border"
      style={{
        background: "rgba(245,166,35,0.08)",
        borderColor: COLORS.amber,
      }}
    >
      <div className="flex items-center justify-between mb-2">
        <div
          className="text-xs uppercase tracking-wider font-semibold"
          style={{ color: COLORS.amber }}
        >
          Needs your approval
        </div>
        {riskScore != null && (
          <div
            className="text-xs font-mono px-2 py-0.5 rounded border"
            style={{
              borderColor: riskScore >= 70 ? COLORS.red : COLORS.amber,
              color: riskScore >= 70 ? COLORS.red : COLORS.amber,
              background: "rgba(0,0,0,0.2)",
            }}
          >
            Risk Score: {riskScore.toFixed(0)}/100
          </div>
        )}
      </div>

      <div className="text-sm" style={{ color: COLORS.ink }}>
        <span className="font-semibold">{tx.agent ? tx.agent.name : request.agent_id}</span>{" "}
        wants to spend{" "}
        <span className="tabular-nums font-semibold">
          &#8377;{Math.round(request.amount)}
        </span>{" "}
        for &ldquo;{request.description}&rdquo;.
      </div>
      <div className="mt-2 text-sm" style={{ color: COLORS.muted }}>
        {tx.reason}
      </div>

      {tx.risk_factors && tx.risk_factors.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {tx.risk_factors.map((f, i) => (
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

      <div className="mt-3 flex gap-2">
        <button
          disabled={busy}
          onClick={() => act("approve")}
          className="text-sm px-4 py-2 rounded-lg font-medium disabled:opacity-50"
          style={{ background: COLORS.green, color: COLORS.bg }}
        >
          Approve
        </button>
        <button
          disabled={busy}
          onClick={() => act("deny")}
          className="text-sm px-4 py-2 rounded-lg font-medium disabled:opacity-50"
          style={{ background: COLORS.red, color: COLORS.bg }}
        >
          Deny
        </button>
      </div>

      {err && (
        <div className="mt-2 text-xs" style={{ color: COLORS.red }}>
          {err}
        </div>
      )}
    </section>
  );
}
