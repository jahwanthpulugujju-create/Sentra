-- Schema for the Judgment Layer ledger. Run once in the Supabase SQL editor.
-- Source of truth: Docs/BUILD_PLAN.md §4. Do not change column names/types
-- without updating the plan first.

-- Agents: each is an identity with a task, a budget, and a live balance.
create table if not exists agents (
    id          text primary key,              -- slug: 'founder','developer',...
    name        text not null,
    task        text not null,
    budget      numeric not null,              -- original allowance (rupees)
    balance     numeric not null,              -- remaining; decremented on spend
    created_at  timestamptz not null default now()
);

-- Transactions: the append-only audit ledger. Every outcome is recorded.
create table if not exists transactions (
    id            uuid primary key default gen_random_uuid(),
    agent_id      text not null references agents(id),
    amount        numeric not null,
    description   text not null,
    decision      text not null,               -- 'allow' | 'escalate' | 'deny'
    status        text not null,               -- 'allowed'|'denied'|'pending'|'approved'
    reason        text not null,               -- plain-English, from the deciding check
    triggered_by  text,                         -- 'rule_engine'|'intent_match'|'anomaly'|null
    intent_source text,                          -- 'llm' | 'fallback' | null
    checks        jsonb not null,               -- full detail of all 3 checks
    created_at    timestamptz not null default now(),
    resolved_at   timestamptz                   -- set when a human resolves an escalation
);

create index if not exists idx_tx_agent_created on transactions (agent_id, created_at desc);
create index if not exists idx_tx_created on transactions (created_at desc);
