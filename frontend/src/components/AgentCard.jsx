import { COLORS, budgetColor } from "../theme";

export default function AgentCard({ agent }) {
  const ratio = agent.budget > 0 ? agent.balance / agent.budget : 0;
  const pct = Math.max(0, Math.min(100, ratio * 100));
  return (
    <div
      className="rounded-xl p-4 border backdrop-blur-md shadow-glass hover:scale-[1.02] transition-all duration-300"
      style={{ background: COLORS.panel, borderColor: COLORS.line }}
    >
      <div className="font-medium" style={{ color: COLORS.ink }}>
        {agent.name}
      </div>
      <div className="text-xs mt-0.5" style={{ color: COLORS.muted }}>
        {agent.task}
      </div>
      <div
        className="mt-3 h-1.5 rounded-full overflow-hidden"
        style={{ background: COLORS.line }}
      >
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${pct}%`, background: budgetColor(ratio) }}
        />
      </div>
      <div
        className="mt-1.5 text-xs tabular-nums"
        style={{ color: COLORS.faint }}
      >
        &#8377;{Math.round(agent.balance)} / &#8377;{Math.round(agent.budget)}
      </div>
    </div>
  );
}
