"""Standalone reference agent (BUILD_PLAN §8A.6) — STRETCH / demo only.

A real Claude agent that, mid-task, emits a `request_payment` tool call. The
HARNESS (this code) — not the model — forwards each call to the live policy
engine at POST /evaluate-transaction and returns the verdict to the agent. The
agent can only ASK; only an Allow ever reaches a real rail.

SECURITY (BUILD_PLAN §14): the agent's identity (AGENT_ID) is a constant set
here, NOT a tool parameter — the model cannot choose whose budget it spends.

Isolated from backend/ and frontend/. Deleting agent_demo/ has zero effect on
the core demo.

Run:
    1) Start the backend (repo README) — /health must show db_connected: true.
    2) Set ANTHROPIC_API_KEY (the agent needs a real LLM — there is no fallback).
    3) py -m venv agent_demo/.venv
       agent_demo/.venv/Scripts/python.exe -m pip install -r agent_demo/requirements.txt
       agent_demo/.venv/Scripts/python.exe agent_demo/run_agent.py
"""
import os
import sys

import requests

try:
    import anthropic
except ImportError:
    sys.exit("Install deps first: pip install -r agent_demo/requirements.txt")

API_BASE = os.getenv("JUDGMENT_API_BASE", "http://localhost:8000")
AGENT_MODEL = os.getenv("AGENT_MODEL", "claude-opus-4-8")

# The agent's identity — set by the HARNESS here, NEVER by the model
# (BUILD_PLAN §14). It is deliberately not a tool parameter.
AGENT_ID = "developer"

# Change this task to exercise different decisions:
#   an image API (~₹40)  -> Allow    |   a GPU cluster (₹5,000) -> Escalate
TASK_PROMPT = (
    "You are the Developer Agent whose job is to build the landing page. "
    "You need a hero image — use your payment tool to buy one from Unsplash "
    "for about 40 rupees."
)

# The agent-facing tool. Note: NO `agent_id` field — the agent cannot choose
# which identity/budget it spends as (BUILD_PLAN §8A.5, §14).
REQUEST_PAYMENT_TOOL = {
    "name": "request_payment",
    "description": (
        "Request a payment on behalf of this agent. This does NOT spend money "
        "directly — every request is screened first and may be allowed, "
        "escalated to a human, or denied."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "vendor": {"type": "string", "description": "Who is being paid"},
            "amount": {"type": "number", "description": "Amount in rupees"},
            "reason": {"type": "string", "description": "Why this serves the task"},
        },
        "required": ["vendor", "amount", "reason"],
    },
}


def screen(amount, reason):
    """STEP 3: forward the payment request to the policy engine (the platform).

    The identity is injected here — the model never sees or sets it.
    """
    try:
        r = requests.post(
            f"{API_BASE}/evaluate-transaction",
            json={"agent_id": AGENT_ID, "amount": amount, "description": reason},
            timeout=30,
        )
    except requests.RequestException as e:
        return {"decision": "error", "reason": f"backend unreachable: {e}"}
    if r.status_code != 200:
        return {"decision": "error", "reason": f"{r.status_code} {r.text}"}
    return r.json()


def main():
    if not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY — the agent needs a real LLM (no fallback).")

    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": TASK_PROMPT}]

    for _ in range(6):  # safety cap on the agentic loop
        resp = client.messages.create(
            model=AGENT_MODEL,
            max_tokens=1024,
            tools=[REQUEST_PAYMENT_TOOL],
            messages=messages,
        )

        for block in resp.content:
            if block.type == "text" and block.text.strip():
                print(f"[agent] {block.text.strip()}")

        if resp.stop_reason != "tool_use":
            break

        messages.append({"role": "assistant", "content": resp.content})
        results = []
        for block in resp.content:
            if block.type == "tool_use" and block.name == "request_payment":
                amount = block.input.get("amount")
                reason = block.input.get("reason", "")
                vendor = block.input.get("vendor", "")
                print(f"[agent -> platform] request_payment: {vendor} ₹{amount} — {reason}")
                # The harness forwards to the policy engine — it does NOT spend here.
                decision = screen(amount, reason)
                verdict = f"{decision['decision'].upper()}: {decision.get('reason', '')}"
                print(f"[platform -> agent] {verdict}")
                # (Optional deeper: on ESCALATE, poll GET /transactions until a human
                #  resolves the pending row in the dashboard, then return the final
                #  verdict here so the agent can continue.)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": verdict,
                })
        messages.append({"role": "user", "content": results})

    print("[done]")


if __name__ == "__main__":
    main()
