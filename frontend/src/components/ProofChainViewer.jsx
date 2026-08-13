import React, { useState } from "react";
import { COLORS, VERDICT_COLOR } from "../theme";

export default function ProofChainViewer({ events, chainStatus, onVerifyChain, onReplayEvent }) {
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [verifying, setVerifying] = useState(false);

  const handleVerifyClick = async () => {
    setVerifying(true);
    await onVerifyChain();
    setVerifying(false);
  };

  const handleSelectEvent = async (ev) => {
    setSelectedEvent(ev);
    if (onReplayEvent) {
      await onReplayEvent(ev.id);
    }
  };

  return (
    <div
      className="rounded-xl border p-6 shadow-sm mb-6"
      style={{ background: COLORS.card, borderColor: COLORS.border }}
    >
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4 pb-3 border-b" style={{ borderColor: COLORS.line }}>
        <div>
          <h2 className="text-lg font-bold" style={{ color: COLORS.ink }}>
            Hash-Linked Proof Chain Ledger
          </h2>
          <p className="text-xs" style={{ color: COLORS.muted }}>
            Monotonic event sequence with SHA-256 hash chaining: <code>eventHash = SHA256(prevHash + payload)</code>
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <div
            className={`text-xs font-mono px-3 py-1 rounded-md border font-semibold ${
              chainStatus?.valid ? "bg-emerald-50 text-emerald-800 border-emerald-300" : "bg-rose-50 text-rose-800 border-rose-300"
            }`}
          >
            {chainStatus?.valid ? `Chain Verified (${chainStatus.totalVerifiedEvents || 0} events)` : "Chain Integrity Error"}
          </div>

          <button
            onClick={handleVerifyClick}
            disabled={verifying}
            className="px-3 py-1.5 text-xs font-semibold rounded-md border shadow-sm transition hover:bg-slate-100"
            style={{ background: COLORS.surface, color: COLORS.ink, borderColor: COLORS.border }}
          >
            {verifying ? "Auditing..." : "Audit Proof Chain"}
          </button>
        </div>
      </div>

      {events && events.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono border-collapse">
            <thead>
              <tr className="border-b text-slate-500 bg-slate-50" style={{ borderColor: COLORS.line }}>
                <th className="p-2 text-center w-12">Seq</th>
                <th className="p-2">Verdict</th>
                <th className="p-2">Reason Code</th>
                <th className="p-2">Previous Hash</th>
                <th className="p-2">Event Hash</th>
                <th className="p-2 text-right">Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {events.map((ev) => {
                const verdictTheme = VERDICT_COLOR[ev.decision] || VERDICT_COLOR.DENY;
                const isSelected = selectedEvent?.id === ev.id;

                return (
                  <tr
                    key={ev.id}
                    onClick={() => handleSelectEvent(ev)}
                    className={`border-b cursor-pointer transition hover:bg-sky-50 ${
                      isSelected ? "bg-sky-100 font-bold" : ""
                    }`}
                    style={{ borderColor: COLORS.line }}
                  >
                    <td className="p-2 text-center font-bold text-slate-700">#{ev.sequence}</td>
                    <td className="p-2">
                      <span
                        className="px-2 py-0.5 rounded font-bold border"
                        style={{
                          background: verdictTheme.bg,
                          color: verdictTheme.text,
                          borderColor: verdictTheme.border,
                        }}
                      >
                        {ev.decision}
                      </span>
                    </td>
                    <td className="p-2 font-semibold text-slate-800">{ev.reason_code}</td>
                    <td className="p-2 text-slate-500 font-mono text-[11px]">
                      {ev.previous_hash ? ev.previous_hash.slice(0, 14) + "..." : "GENESIS"}
                    </td>
                    <td className="p-2 font-mono font-bold text-sky-800 text-[11px]">
                      {ev.event_hash ? ev.event_hash.slice(0, 14) + "..." : "N/A"}
                    </td>
                    <td className="p-2 text-right text-slate-500 text-[11px]">
                      {ev.created_at ? new Date(ev.created_at).toLocaleTimeString() : ""}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="p-8 text-center text-xs text-slate-500 bg-slate-50 rounded-lg border" style={{ borderColor: COLORS.border }}>
          No authority events recorded yet. Run a scenario above to generate hash-linked proof chain records.
        </div>
      )}

      {selectedEvent && (
        <div className="mt-4 p-4 rounded-lg border bg-slate-900 text-slate-100 font-mono text-xs">
          <div className="flex justify-between items-center mb-2 pb-2 border-b border-slate-700">
            <span className="text-emerald-400 font-bold">Event Audit Evidence Packet #{selectedEvent.sequence}</span>
            <button onClick={() => setSelectedEvent(null)} className="text-slate-400 hover:text-white">✕</button>
          </div>
          <div className="text-[11px] text-slate-400 mb-1">Event Hash: {selectedEvent.event_hash}</div>
          <div className="text-[11px] text-slate-400 mb-2">Previous Hash: {selectedEvent.previous_hash}</div>
          <pre className="text-emerald-300 text-[11px] overflow-x-auto bg-slate-950 p-2 rounded border border-slate-800">
            {JSON.stringify(selectedEvent.payload, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
