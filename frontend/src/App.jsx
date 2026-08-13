import { useCallback, useEffect, useState } from "react";
import { COLORS } from "./theme";
import { getHealth, getDashboard, runScenario, verifyProofChain, resetDemo, getReplay } from "./api";
import HeaderHero from "./components/HeaderHero";
import ScenarioRunner from "./components/ScenarioRunner";
import DecisionInspector from "./components/DecisionInspector";
import ProofChainViewer from "./components/ProofChainViewer";
import AuthorityPlanes from "./components/AuthorityPlanes";
import MvpStatusPanel from "./components/MvpStatusPanel";

export default function App() {
  const [health, setHealth] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [runningScenario, setRunningScenario] = useState(null);
  const [lastScenarioResult, setLastScenarioResult] = useState(null);
  const [activeScenarioId, setActiveScenarioId] = useState(null);
  const [resetting, setResetting] = useState(false);

  const fetchState = useCallback(async () => {
    try {
      const [h, d] = await Promise.all([getHealth(), getDashboard()]);
      setHealth(h);
      setDashboard(d);
    } catch (e) {
      console.error("Failed to fetch state", e);
    }
  }, []);

  useEffect(() => {
    fetchState();
    const interval = setInterval(fetchState, 3000);
    return () => clearInterval(interval);
  }, [fetchState]);

  const handleRunScenario = async (scenarioId) => {
    setRunningScenario(scenarioId);
    setActiveScenarioId(scenarioId);
    try {
      const res = await runScenario(scenarioId);
      setLastScenarioResult(res);
      await fetchState();
    } catch (e) {
      setLastScenarioResult({
        verdict: "DENY",
        reasonCode: "EXECUTION_ERROR",
        explanation: String(e.message || e),
        stateChanged: false,
      });
    } finally {
      setRunningScenario(null);
    }
  };

  const handleResetBaseline = async () => {
    setResetting(true);
    try {
      await resetDemo();
      setLastScenarioResult(null);
      setActiveScenarioId(null);
      await fetchState();
    } catch (e) {
      console.error("Reset failed", e);
    } finally {
      setResetting(false);
    }
  };

  const handleVerifyChain = async () => {
    try {
      const verifyRes = await verifyProofChain();
      setDashboard((prev) =>
        prev
          ? {
              ...prev,
              proofChainStatus: {
                valid: verifyRes.valid,
                errorMessage: verifyRes.errorMessage,
                totalVerifiedEvents: verifyRes.totalEventsVerified,
              },
            }
          : prev
      );
    } catch (e) {
      console.error("Chain verification failed", e);
    }
  };

  const handleReplayEvent = async (eventId) => {
    try {
      const rep = await getReplay(eventId);
      console.log("Replayed event", rep);
    } catch (e) {
      console.error("Replay fetch failed", e);
    }
  };

  const resourceObj = dashboard?.resources?.find((r) => r.id === "prod_k8s_cluster")?.state;

  return (
    <div style={{ minHeight: "100vh", background: COLORS.bg, color: COLORS.ink }} className="p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header & Hero Pipeline Artifact */}
        <HeaderHero health={health} onReset={handleResetBaseline} resetting={resetting} />

        {/* Live Boundary Test: 6 Mandatory Scenarios */}
        <ScenarioRunner
          onRunScenario={handleRunScenario}
          runningId={runningScenario}
          activeScenarioId={activeScenarioId}
        />

        {/* Decision Inspector */}
        <DecisionInspector lastResult={lastScenarioResult} resourceState={resourceObj} />

        {/* Proof Chain Timeline & Verifier */}
        <ProofChainViewer
          events={dashboard?.recentEvents || []}
          chainStatus={dashboard?.proofChainStatus}
          onVerifyChain={handleVerifyChain}
          onReplayEvent={handleReplayEvent}
        />

        {/* Four Authority Planes */}
        <AuthorityPlanes />

        {/* MVP Status & Closing Banner */}
        <MvpStatusPanel />
      </div>
    </div>
  );
}
