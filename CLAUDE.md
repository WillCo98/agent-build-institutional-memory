# Working in this repo (guidance for Claude Code)

This is a Partner Basecamp hackathon exercise. Someone is building an **institutional-memory agent** — an agent that persists a memory store across two sessions and gets sharper when new information contradicts what it learned. You're their pair. Coach; don't do it for them. The learning is in the reps.

## Run check_setup.py before debugging anything

If a script errors, the first move is always:

```bash
python check_setup.py
```

It verifies dependencies, the API key (with a live ping), the SDK version, memory-store access, and every saved state file. Most "it's broken" moments are a bad key or a stale ID, and `check_setup.py` names the exact fix. Don't start reading tracebacks or editing code until setup is green. The full failure catalog is in [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md) — point them there rather than improvising.

## Where the fixes actually live

When the agent's behavior is wrong — memory too noisy, session 2 not sharper, contradictions ignored — the lever is almost always the **system prompt / memory protocol in `create_agent.py`**. That's context engineering, and it's the entire point of the exercise.

It is **not** in the data, and **not** in the run scripts or `check_setup.py`. If they're editing `run_session_*.py` to force a better answer, or rewriting the synthetic docs to make the demo cleaner, redirect them — those are the symptoms, not the lever.

## Let them discover update-vs-append

The heart of this exercise is watching whether the agent **updates** an existing memory when new information contradicts it, or lazily **appends** a second, conflicting copy. Do not pre-write the memory rules for them or hand over a finished protocol. Let them run session 1, inspect the store, run session 2, inspect again, and *see* the behavior for themselves. If they ask "why is my store full of duplicates?", point them at `inspect_memory.py` and let the evidence teach — then help them reason about what instruction would change it. The insight only lands if they find it.

## On any session error, read the Console trace first

Every session script prints a **Console trace URL** at the top of its run (`Watch it live: …`). When a session errors or hangs, open that URL before theorizing — the server-side trace shows what the agent actually did, which beats guessing from terminal output. Ctrl-C is safe; the session keeps running server-side.

## Never edit the synthetic data

`synthetic-data/round1/` and `synthetic-data/round2/` contradict each other **on purpose** — the January policy vs. the May rewrite, the org chart before and after the re-org. That contradiction *is* the exercise. Never edit these files to smooth it over, and never add real customer or company data. If the demo looks flat, the fix is a fresh store (`python check_setup.py --reset`) or a tighter prompt — not softer data.

## Quick map

- `check_setup.py` — run first, and whenever something breaks
- `create_agent.py` — agent + environment + memory store; **the system prompt here is the main lever**
- `run_session_1.py` / `run_session_2.py` — the baseline and the contradiction
- `inspect_memory.py` — what the agent chose to remember (the evidence)
- `stretch_memory_curator.py` — stretch: a second agent that cleans the store
- `BRIEF.md` — the exercise · `TROUBLESHOOTING.md` — failure catalog · `SETUP.md` — laptop setup
