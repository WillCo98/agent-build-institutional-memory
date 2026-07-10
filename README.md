# Track 2 — Institutional Memory Agent

Build an agent that runs two sessions on the same domain with a [memory store](https://platform.claude.com/docs/en/managed-agents/memory) persisting between them. Memory here doesn't mean "a vector database for documents" — it means the agent decides what to remember, what to update, and what to forget when new information contradicts what it learned. New docs in session 2 contradict session 1; a good agent reconciles them and answers visibly sharper the second time. [Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview) runs the sessions in the cloud — nothing to spin up locally.

**Start with [`BRIEF.md`](./BRIEF.md)** — the scenario, the 40-minute plan, the demo, and how to re-point it at your own domain.

## Step 0 — always

```bash
git clone https://github.com/victorsteeb/agent-build-institutional-memory.git
cd agent-build-institutional-memory
python check_setup.py
```

`check_setup.py` installs the SDK if needed, sets up your key in a gitignored `.env`, pings the API, confirms memory-store access, and validates any saved state. Green means the plumbing is done and everything after is the exercise. If it isn't green, [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md) has the fix; on a new or locked-down laptop, [`SETUP.md`](./SETUP.md) has the one-page venv-and-proxy setup.

## How to run

Work the exercise in the repo — never by pasting code out of a chat window. `check_setup.py` handles the key (a gitignored `.env`, or an `ANTHROPIC_API_KEY` shell variable); you need a **workspace** key from the Console.

### VS Code / Cursor (recommended)
1. **File → Open Folder** and select this repo.
2. Install the **Python** extension if prompted.
3. Open a terminal, run `python check_setup.py`, then run the scripts in the order `BRIEF.md` lays out.

### Claude Code (CLI)
`cd` into the repo, prove setup, then run the build end to end or pair with Claude Code on it:

```bash
cd agent-build-institutional-memory
python check_setup.py
python create_agent.py       # then run_session_1 → inspect_memory → run_session_2
claude                       # …or work the exercise with Claude Code as your pair
```

There's a `CLAUDE.md` in here that briefs Claude Code on how to coach rather than solve.

### Claude Desktop
Keep it open alongside as your AI pair — ask it to explain the memory protocol, reason about a store that filled with duplicates, or debug an error while you edit.

## File map

```
agent-build-institutional-memory/
├── BRIEF.md                    the exercise — read this first
├── check_setup.py              run before anything else (deps, key, SDK, state)
├── create_agent.py             agent + environment + memory store (idempotent)
├── run_session_1.py            session 1 — round1 docs, baseline answer
├── run_session_2.py            session 2 — round2 contradictions, same question
├── inspect_memory.py           list what the agent chose to remember
├── stretch_memory_curator.py   stretch: curator sub-agent on the same store
├── synthetic-data/
│   ├── round1/                 initial context — handbook, directory, access policy
│   └── round2/                 the updates that contradict round 1
├── TROUBLESHOOTING.md          every failure mode and its fix
├── SETUP.md                    venv / PEP 668 / proxy / no-admin / key
├── stretch-goals.md            pick one after the core build
└── CLAUDE.md                   how Claude Code should coach in this repo
```

## The pitch, in one line

Same question, two sessions, visibly sharper answer — and you can show exactly what the agent chose to remember. That's the memory-stores story enterprise clients keep asking for.
