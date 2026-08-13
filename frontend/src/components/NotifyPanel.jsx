import { useState } from "react";
import { COLORS } from "../theme";
import { publishTest } from "../ntfy";

export default function NotifyPanel({ topic, enabled, onToggle }) {
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);

  const test = async () => {
    setBusy(true);
    setMsg(null);
    try {
      const r = await publishTest(topic);
      setMsg(r.ok ? "Test sent — check your phone." : `Failed (${r.status}).`);
    } catch (e) {
      setMsg(String(e.message || e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section
      className="rounded-xl p-4 border backdrop-blur-md shadow-glass"
      style={{ background: COLORS.panel, borderColor: COLORS.line }}
    >
      <div
        className="text-xs uppercase tracking-wider mb-2"
        style={{ color: COLORS.faint }}
      >
        Phone push (ntfy.sh)
      </div>

      <ol className="text-sm space-y-1" style={{ color: COLORS.muted }}>
        <li>1. Install the free <b>ntfy</b> app (Android / iOS).</li>
        <li>2. In the app, subscribe to this topic:</li>
      </ol>
      <div
        className="my-2 font-mono text-sm px-3 py-2 rounded-lg"
        style={{ background: COLORS.panelAlt, color: COLORS.ink, wordBreak: "break-all" }}
      >
        {topic}
      </div>

      <div className="flex gap-2">
        <button
          onClick={onToggle}
          className="text-sm px-3 py-2 rounded-lg font-medium"
          style={{ background: enabled ? COLORS.green : COLORS.amber, color: COLORS.bg }}
        >
          {enabled ? "Phone push ON" : "Enable phone push"}
        </button>
        <button
          onClick={test}
          disabled={busy}
          className="text-sm px-3 py-2 rounded-lg border disabled:opacity-50"
          style={{ borderColor: COLORS.line, color: COLORS.muted }}
        >
          {busy ? "Sending…" : "Send test"}
        </button>
      </div>

      {msg && (
        <div className="mt-2 text-xs" style={{ color: COLORS.faint }}>
          {msg}
        </div>
      )}
      <div className="mt-2 text-xs" style={{ color: COLORS.faint }}>
        On escalation your phone gets an Approve/Deny prompt — tapping it resolves
        the transaction live here. Public ntfy.sh relay; topic is randomized. Most
        reliable on Android.
      </div>
    </section>
  );
}
