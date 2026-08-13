import { COLORS, STATUS_COLOR } from "../theme";

export default function AuditRow({ tx }) {
  const c = STATUS_COLOR[tx.status] || COLORS.muted;
  const time = new Date(tx.created_at).toLocaleTimeString();
  const src = tx.intent_source ? ` · ${tx.intent_source}` : "";
  const risk = tx.risk_score != null ? ` · Risk ${Math.round(tx.risk_score)}` : "";

  return (
    <div
      className="grid grid-cols-12 gap-2 items-center py-2 border-b text-sm"
      style={{ borderColor: COLORS.line }}
    >
      <div className="col-span-3 sm:col-span-2 font-mono text-xs" style={{ color: COLORS.faint }}>
        {time}
      </div>
      <div className="col-span-3 sm:col-span-2 truncate font-medium" style={{ color: COLORS.ink }}>
        {tx.agent_id}
      </div>
      <div className="col-span-2 sm:col-span-1 tabular-nums text-right font-mono" style={{ color: COLORS.ink }}>
        &#8377;{Math.round(tx.amount)}
      </div>
      <div className="col-span-4 sm:col-span-2">
        <span
          className="text-xs font-semibold uppercase px-2 py-0.5 rounded"
          style={{ color: c, border: `1px solid ${c}` }}
        >
          {tx.status}
        </span>
      </div>
      <div className="col-span-12 sm:col-span-5 truncate text-xs" style={{ color: COLORS.muted }}>
        {tx.reason}
        <span className="font-mono text-faint">{src}{risk}</span>
      </div>
    </div>
  );
}
