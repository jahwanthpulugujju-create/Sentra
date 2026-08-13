// Phone push via ntfy.sh — no custom backend needed (PROJECT_BRIEF §5.1).
// On escalation we publish a notification with Approve/Deny action buttons that
// POST to a second "<topic>-action" topic; the browser subscribes to that topic
// over SSE, so tapping the phone resolves the transaction live in the dashboard.
const NTFY = "https://ntfy.sh";

export function actionTopic(topic) {
  return `${topic}-action`;
}

// Publish the approval prompt to the phone.
export async function publishEscalation(topic, { txId, agentName, amount, description, reason }) {
  const at = actionTopic(topic);
  const payload = {
    topic,
    title: "Approval needed",
    message: `${agentName} wants ₹${Math.round(amount)} for "${description}". ${reason}`,
    priority: 5,
    tags: ["warning", "moneybag"],
    actions: [
      { action: "http", label: "Approve", url: `${NTFY}/${at}`, method: "POST", body: `approve|${txId}`, clear: true },
      { action: "http", label: "Deny", url: `${NTFY}/${at}`, method: "POST", body: `deny|${txId}`, clear: true },
    ],
  };
  return fetch(NTFY, { method: "POST", body: JSON.stringify(payload) });
}

// A plain test ping so the presenter can confirm the phone is subscribed.
export async function publishTest(topic) {
  return fetch(`${NTFY}/${topic}`, {
    method: "POST",
    body: "Test from the Judgment Layer — your phone is connected.",
  });
}

// Subscribe to phone taps. Returns the EventSource so the caller can close it.
export function subscribeDecisions(topic, onDecision) {
  const es = new EventSource(`${NTFY}/${actionTopic(topic)}/sse`);
  es.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      if (data.event !== "message" || !data.message) return;
      const [action, txId] = String(data.message).split("|");
      if ((action === "approve" || action === "deny") && txId) {
        onDecision(action, txId);
      }
    } catch {
      /* ignore open/keepalive events */
    }
  };
  return es;
}
