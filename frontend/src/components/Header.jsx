import { useEffect, useState } from "react";
import { COLORS } from "../theme";
import { getHealth, reset } from "../api";

function HealthBadge() {
  const [h, setH] = useState(null);
  useEffect(() => {
    let active = true;
    const tick = async () => {
      try {
        const d = await getHealth();
        if (active) setH(d);
      } catch {
        if (active) setH(null);
      }
    };
    tick();
    const id = setInterval(tick, 4000);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, []);

  let color = COLORS.red;
  let label = "Offline";
  if (h && h.db_connected && h.llm_configured) {
    color = COLORS.green;
    label = "Live · LLM connected";
  } else if (h && h.db_connected && !h.llm_configured) {
    color = COLORS.amber;
    label = "Live · fallback (no key)";
  }

  return (
    <div className="flex items-center gap-2 text-sm">
      <span
        className="inline-block w-2 h-2 rounded-full"
        style={{ background: color }}
      />
      <span style={{ color: COLORS.ink }}>{label}</span>
    </div>
  );
}

function ResetButton({ onReset }) {
  const [busy, setBusy] = useState(false);
  const click = async () => {
    setBusy(true);
    try {
      await reset();
      if (onReset) await onReset();
    } finally {
      setBusy(false);
    }
  };
  return (
    <button
      onClick={click}
      disabled={busy}
      className="text-sm px-3 py-1.5 rounded-md border transition-all duration-300 disabled:opacity-50 hover:bg-white/5 hover:text-white"
      style={{ borderColor: COLORS.line, color: COLORS.muted }}
    >
      {busy ? "Resetting…" : "Reset demo"}
    </button>
  );
}

export default function Header({ onReset }) {
  return (
    <header className="flex items-center justify-between py-5 animate-fade-in">
      <div className="flex items-center gap-3">
        <div
          className="w-8 h-8 rounded-lg grid place-items-center font-bold shadow-glow-amber transition-transform hover:scale-110"
          style={{ background: COLORS.amber, color: COLORS.bg }}
        >
          S
        </div>
        <div>
          <div className="font-semibold tracking-tight" style={{ color: COLORS.ink }}>
            Sentra
          </div>
          <div className="text-xs" style={{ color: COLORS.faint }}>
            The Judgment Layer for Autonomous AI Payments
          </div>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <HealthBadge />
        <ResetButton onReset={onReset} />
      </div>
    </header>
  );
}
