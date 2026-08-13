import AgentCard from "./AgentCard";
import { COLORS } from "../theme";

export default function AgentRoster({ agents }) {
  return (
    <section>
      <div
        className="text-xs uppercase tracking-wider mb-2"
        style={{ color: COLORS.faint }}
      >
        Agents
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {(agents || []).map((a) => (
          <AgentCard key={a.id} agent={a} />
        ))}
        {(!agents || agents.length === 0) && (
          <div className="text-sm" style={{ color: COLORS.faint }}>
            Waiting for agents…
          </div>
        )}
      </div>
    </section>
  );
}
