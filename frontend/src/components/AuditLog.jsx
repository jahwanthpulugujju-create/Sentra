import AuditRow from "./AuditRow";
import { COLORS } from "../theme";

export default function AuditLog({ transactions }) {
  const rows = transactions || [];
  return (
    <section
      className="rounded-xl p-4 border backdrop-blur-md shadow-glass"
      style={{ background: COLORS.panel, borderColor: COLORS.line }}
    >
      <div
        className="text-xs uppercase tracking-wider mb-2"
        style={{ color: COLORS.faint }}
      >
        Audit log
      </div>
      <div className="max-h-[360px] overflow-y-auto pr-1">
        {rows.length === 0 && (
          <div className="text-sm py-4" style={{ color: COLORS.faint }}>
            No transactions yet.
          </div>
        )}
        {rows.map((tx) => (
          <AuditRow key={tx.id} tx={tx} />
        ))}
      </div>
    </section>
  );
}
