import { useEffect, useState } from "react";
import { COLORS } from "./theme";
import { getAgents, getTransactions, evaluate, resolve } from "./api";
import { usePolling } from "./hooks/usePolling";
import { publishEscalation, subscribeDecisions } from "./ntfy";
import Header from "./components/Header";
import AgentRoster from "./components/AgentRoster";
import RequestPanel from "./components/RequestPanel";
import ProcessingPanel from "./components/ProcessingPanel";
import EscalationCard from "./components/EscalationCard";
import MetricsPanel from "./components/MetricsPanel";
import NotifyPanel from "./components/NotifyPanel";
import AuditLog from "./components/AuditLog";

function getTopic() {
  let t = localStorage.getItem("ntfy_topic");
  if (!t) {
    const rand = (
      window.crypto && crypto.randomUUID
        ? crypto.randomUUID()
        : Math.random().toString(36).slice(2)
    )
      .replace(/-/g, "")
      .slice(0, 10);
    t = `sentra-${rand}`;
    localStorage.setItem("ntfy_topic", t);
  }
  return t;
}

export default function App() {
  const agentsPoll = usePolling(getAgents, 2000);
  const txPoll = usePolling(() => getTransactions(50), 2000);
  const [proc, setProc] = useState({ running: false, result: null, request: null });
  const [topic] = useState(getTopic);
  const [pushEnabled, setPushEnabled] = useState(false);

  const refreshAll = async () => {
    await Promise.all([agentsPoll.refresh(), txPoll.refresh()]);
  };

  const runEvaluate = async (body) => {
    setProc({ running: true, result: null, request: body });
    try {
      const res = await evaluate(body);
      setProc({ running: false, result: res, request: body });
      await refreshAll();
      if (pushEnabled && res.decision === "escalate" && res.status === "pending") {
        publishEscalation(topic, {
          txId: res.transaction_id,
          agentName: res.agent ? res.agent.name : body.agent_id,
          amount: body.amount,
          description: body.description,
          reason: res.reason,
        }).catch(() => {});
      }
    } catch (e) {
      setProc({
        running: false,
        result: { decision: "error", reason: String(e.message || e) },
        request: body,
      });
    }
  };

  const onResolved = async () => {
    setProc((p) => ({ ...p, result: null }));
    await refreshAll();
  };

  // Resolve triggered by a phone tap (via ntfy SSE).
  const resolveFromPhone = async (action, txId) => {
    try {
      await resolve({ transaction_id: txId, action });
      setProc((p) =>
        p.result && p.result.transaction_id === txId ? { ...p, result: null } : p
      );
      await refreshAll();
    } catch {
      /* already resolved / stale — ignore */
    }
  };

  // Subscribe to phone decisions while push is enabled.
  useEffect(() => {
    if (!pushEnabled) return undefined;
    const es = subscribeDecisions(topic, resolveFromPhone);
    return () => es.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pushEnabled, topic]);

  const offline = agentsPoll.error && !agentsPoll.data;
  const pendingEscalation =
    proc.result &&
    proc.result.decision === "escalate" &&
    proc.result.status === "pending";

  return (
    <div style={{ minHeight: "100%", background: COLORS.bg, color: COLORS.ink }}>
      <div className="max-w-6xl mx-auto px-4 pb-12">
        <Header onReset={refreshAll} />

        {offline && (
          <div
            className="mb-4 text-sm px-3 py-2 rounded-lg border"
            style={{ borderColor: COLORS.red, color: COLORS.red }}
          >
            Can&apos;t reach the backend at the API base URL. Make sure the
            backend is running on port 8000 (`/health` shows db_connected: true).
          </div>
        )}

        <div className="space-y-4">
          <AgentRoster agents={agentsPoll.data} />
          <MetricsPanel />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="space-y-4">
              <RequestPanel
                agents={agentsPoll.data}
                onRun={runEvaluate}
                running={proc.running}
              />
              <ProcessingPanel running={proc.running} result={proc.result} />
              {pendingEscalation && (
                <EscalationCard
                  tx={proc.result}
                  request={proc.request}
                  onResolved={onResolved}
                />
              )}
            </div>
            <div className="space-y-4">
              <AuditLog transactions={txPoll.data} />
              <NotifyPanel
                topic={topic}
                enabled={pushEnabled}
                onToggle={() => setPushEnabled((v) => !v)}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
