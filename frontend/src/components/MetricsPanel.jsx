import { useEffect, useState } from "react";
import { COLORS } from "../theme";
import { getMetrics } from "../api";

export default function MetricsPanel() {
  const [metrics, setMetrics] = useState(null);

  const fetchMetrics = async () => {
    try {
      const data = await getMetrics();
      setMetrics(data);
    } catch {
      /* ignore polling errors */
    }
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 3000);
    return () => clearInterval(interval);
  }, []);

  if (!metrics || metrics.total_transactions === 0) {
    return (
      <section
        className="rounded-xl p-4 border backdrop-blur-md shadow-glass"
        style={{ background: COLORS.panel, borderColor: COLORS.line }}
      >
        <div className="text-xs uppercase tracking-wider mb-2" style={{ color: COLORS.faint }}>
          Evaluation Metrics
        </div>
        <div className="text-xs" style={{ color: COLORS.muted }}>
          No metrics available yet. Run transactions to see live analytics.
        </div>
      </section>
    );
  }

  return (
    <section
      className="rounded-xl p-4 border backdrop-blur-md shadow-glass"
      style={{ background: COLORS.panel, borderColor: COLORS.line }}
    >
      <div className="text-xs uppercase tracking-wider mb-3" style={{ color: COLORS.faint }}>
        Evaluation Metrics & Threat Analytics
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-2.5 rounded-lg border" style={{ background: COLORS.panelAlt, borderColor: COLORS.line }}>
          <div className="text-xs" style={{ color: COLORS.faint }}>Total Evaluation</div>
          <div className="text-lg font-bold font-mono" style={{ color: COLORS.ink }}>
            {metrics.total_transactions}
          </div>
        </div>

        <div className="p-2.5 rounded-lg border" style={{ background: COLORS.panelAlt, borderColor: COLORS.line }}>
          <div className="text-xs" style={{ color: COLORS.faint }}>Threat Detection</div>
          <div className="text-lg font-bold font-mono" style={{ color: COLORS.amber }}>
            {metrics.threat_detection_rate}%
          </div>
        </div>

        <div className="p-2.5 rounded-lg border" style={{ background: COLORS.panelAlt, borderColor: COLORS.line }}>
          <div className="text-xs" style={{ color: COLORS.faint }}>Escalation Rate</div>
          <div className="text-lg font-bold font-mono" style={{ color: COLORS.amber }}>
            {metrics.escalation_rate}%
          </div>
        </div>

        <div className="p-2.5 rounded-lg border" style={{ background: COLORS.panelAlt, borderColor: COLORS.line }}>
          <div className="text-xs" style={{ color: COLORS.faint }}>Avg Response Time</div>
          <div className="text-lg font-bold font-mono" style={{ color: COLORS.green }}>
            {metrics.avg_processing_time_ms ? `${metrics.avg_processing_time_ms}ms` : "N/A"}
          </div>
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between text-xs font-mono" style={{ color: COLORS.muted }}>
        <div>
          Decisions: <span style={{ color: COLORS.green }}>{metrics.decisions_breakdown.allow} Allow</span> ·{" "}
          <span style={{ color: COLORS.amber }}>{metrics.decisions_breakdown.escalate} Escalate</span> ·{" "}
          <span style={{ color: COLORS.red }}>{metrics.decisions_breakdown.deny} Deny</span>
        </div>
        <div>
          Engine: <span style={{ color: COLORS.ink }}>{metrics.llm_vs_fallback.llm} LLM</span> /{" "}
          <span style={{ color: COLORS.faint }}>{metrics.llm_vs_fallback.fallback} Fallback</span>
        </div>
      </div>
    </section>
  );
}
