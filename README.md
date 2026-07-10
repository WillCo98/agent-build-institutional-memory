# Track 2 — Institutional Memory Agent

**Concept landed:** Memory & context engineering
**Tech:** [Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview) + [Memory Stores](https://platform.claude.com/docs/en/managed-agents/memory)
**Build window:** ~40 minutes on the clock
**Output:** An agent that visibly gets sharper across multiple sessions on the same domain.

## The pitch

Memory is the concept enterprise clients ask about most and understand least. Most people think it means "a vector database for documents." It doesn't — it means **the agent decides what to remember, what to forget, and what to update when it learns something new.**

You'll build an agent that runs two sessions on the same domain. Between the two sessions, a **memory store** persists — mounted at `/mnt/memory/` inside each session's container, read and written by the agent with its ordinary file tools. New information in session 2 contradicts session 1. The agent should reconcile, update its memory, and answer better than it did the first time.

That's the demo: same question, two sessions, visibly sharper answer.

## Setup (5 min)

You need a workspace API key from the Console (your team's workspace).

```bash
git clone https://github.com/victorsteeb/agent-build-institutional-memory.git
cd agent-build-institutional-memory
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."
```

That's it. No infrastructure to spin up — Managed Agents runs the sessions in the cloud.

## Pick a scenario card

Four cards in [`scenario-cards.md`](./scenario-cards.md). The data in `synthetic-data/` ships ready for **Card A (New-Hire Onboarding)** — the other cards need you to reshape the docs, so only pick them if you're happy spending build time on data.

## Core build

1. **Provision.** `python create_agent.py` — creates the agent (system prompt carries the memory protocol: check memory first, update-don't-append, note dates), the cloud environment, and the memory store. IDs are saved to `.agent_id`, `.environment_id`, `.memory_store_id`. Safe to re-run: it reuses everything it already created.

2. **Session 1 — baseline.** `python run_session_1.py` — starts a session with the memory store attached, hands the agent the `round1` docs, asks the test question, saves the answer to `outputs/session1.txt`. Watch the `[memory: ...]` lines in the stream — that's the agent writing to `/mnt/memory/`.

3. **Look at what it remembered.** `python inspect_memory.py` — lists every memory file the agent chose to write. This is your mid-demo beat.

4. **Session 2 — the contradiction.** `python run_session_2.py` — a **fresh** session, same agent, same store. The `round2` docs contradict round 1. Same question. The answer should lead with what changed, cite the newer policy, and the memory store should show **updated** entries, not appended duplicates.

5. **Compare.** `outputs/session1.txt` vs `outputs/session2.txt` — the demo lives in that diff.

## Stretch goals (pick one)

See [`stretch-goals.md`](./stretch-goals.md).

- **Tier 1 — deliberate memory:** explicit remember/never-remember lists in the system prompt; the Memory Curator sub-agent (`python stretch_memory_curator.py` — a second agent that gets the *same store* mounted and cleans it).
- **Tier 2 — stress-test memory:** an adversarial round-3 with deliberately wrong docs; the "what have you learned?" session.
- **Tier 3 — production-shaped:** per-tenant stores; wire the two-session loop into a scheduled routine.

## Two-minute demo

Three terminals:
- Left: `outputs/session1.txt`
- Right: `outputs/session2.txt` (same question, sharper answer)
- Middle: `python inspect_memory.py` — show what the agent chose to remember, and that it *updated* rather than appended.

Read both answers out loud. Let the room hear the answer sharpen.

## What's in this folder

```
agent-build-institutional-memory/
├── README.md                      (you are here)
├── scenario-cards.md
├── stretch-goals.md
├── requirements.txt
├── create_agent.py                (agent + environment + memory store, idempotent)
├── run_session_1.py               (session 1 — round1 docs, baseline answer)
├── run_session_2.py               (session 2 — round2 contradictions, same question)
├── inspect_memory.py              (list what the agent remembered)
├── stretch_memory_curator.py      (stretch: curator sub-agent on the same store)
└── synthetic-data/
    ├── round1/                    (initial context — handbook, directory, policy)
    └── round2/                    (updates and contradictions)
```
