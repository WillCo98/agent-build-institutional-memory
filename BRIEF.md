# Track 1 — Institutional Memory Agent (build brief)

**Concept landed:** Memory & context engineering
**Tech:** [Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview) + [memory stores](https://platform.claude.com/docs/en/managed-agents/memory)
**Build window:** ~40 minutes on the clock
**Output:** An agent that visibly gets sharper across two sessions on the same domain.

## The shape you're building

Memory is the concept enterprise clients ask about most and understand least. Most people think it means "a vector database for documents." It doesn't — it means **the agent decides what to remember, what to forget, and what to update when it learns something new.**

You'll build an agent that runs two sessions on the same domain. Between them a **memory store** persists — mounted at `/mnt/memory/` inside each session's container, read and written by the agent with its ordinary file tools. New information in session 2 contradicts session 1. The agent should reconcile, update its memory, and answer better than it did the first time.

That's the demo: same question, two sessions, visibly sharper answer. No infrastructure to spin up — Managed Agents runs the sessions in the cloud.

## Step 0 — prove your setup (2 min, before you touch anything)

```bash
git clone https://github.com/victorsteeb/agent-build-institutional-memory.git
cd agent-build-institutional-memory
python check_setup.py
```

`check_setup.py` is the gate. It installs the SDK if it's missing, creates a gitignored `.env` for your key (paste your workspace key in, re-run), pings the API live, confirms your SDK and workspace can use memory stores, and validates any state files from earlier runs. When it prints **All checks passed**, everything after this point is the exercise, not the plumbing. If it doesn't pass, [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md) has the fix — you shouldn't need anyone in the room.

New machine or a locked-down corporate laptop? [`SETUP.md`](./SETUP.md) is the one-page venv-and-proxy fix.

## The scenario — New-Hire Onboarding

One wired scenario, ready to run — the synthetic data in `synthetic-data/` is already shaped for it.

**The agent:** an onboarding assistant for new engineering hires at a fast-growing company ("How do I get prod access?", "Who owns the payment service?", "What's our git workflow?").

**Round 1 (`synthetic-data/round1/`):** the onboarding handbook, the team directory, and the production access policy — the world as it stood in January.

**Round 2 (`synthetic-data/round2/`):** a May policy update that rewrites the prod-access workflow, and a team directory rewritten after a re-org. These *contradict* round 1 on purpose — the January answer is now wrong.

**The test question (identical in both sessions):**
> "I just joined the company and I need read-only prod access to debug an issue tomorrow. What do I do? Be specific about the steps and the people I need to talk to."

**What a sharper session-2 answer looks like:** it leads with what changed, cites the newer policy (self-serve certification + just-in-time IAM access, effective 2026-05-15), does *not* recommend the retired workflow (the `#sre-access-requests` Slack ticket and the SRE pairing session are gone), and the memory store shows **updated** entries, not appended duplicates. If the agent still routes the new hire to the old Slack ticket, memory didn't do its job — and noticing that is the skill, not a failure of the exercise.

## Core build

Run these in order. Every session script prints its **session ID and a Console trace URL at the top** — keep that URL; it's how you watch a run live and how you diagnose anything that stalls.

1. **Provision.** `python create_agent.py` — creates the agent (`claude-sonnet-5`; its system prompt carries the memory protocol: check memory first, update-don't-append, note dates), the cloud environment, and the memory store. IDs are saved to `.agent_id`, `.environment_id`, `.memory_store_id`. Safe to re-run — it reuses everything it already created.

2. **Session 1 — the baseline.** `python run_session_1.py` — opens a session with the memory store attached, hands the agent the `round1` docs, asks the test question, saves the answer to `outputs/session1.txt`. Watch the `[memory: ...]` lines stream past — that's the agent writing to `/mnt/memory/`.

3. **Look at what it remembered.** `python inspect_memory.py` — lists every memory file the agent chose to write (add `--full` for the contents). This is your mid-demo beat, and your evidence that session 1 actually wrote memory.

4. **Session 2 — the contradiction.** `python run_session_2.py` — a **fresh** session, same agent, same store. The `round2` docs contradict round 1. Same question. The answer should lead with what changed, cite the newer policy, and the store should show *updated* entries, not appended duplicates.

5. **Compare.** `outputs/session1.txt` vs `outputs/session2.txt` — the demo lives in that diff.

6. **Verify it.** `python check_memory.py` — the required check, and the habit: "session 2 felt sharper" is not the same as "memory did its job." No second model — a fast local read of the session-2 answer and the store. It gates on a scenario-agnostic **floor** (a real session-2 answer exists), and — while you're on the wired onboarding scenario — grades the "Done when" bar for free (the retired workflow is gone from the answer, the current policy is cited, the store looks **updated, not appended**) as advisory guidance. **Adapting the scenario? The check comes with you:** drop an `acceptance.txt` next to the script — one criterion per line (plain text, `/regex/`, or `!must-not`) — and it grades *your* domain against *your* bar. If it flags a problem, the lever is the memory protocol in `create_agent.py` — never the data.

## The 40 minutes

- **0–5 — prove setup.** `python check_setup.py` until it's all green. Don't build on an unproven key.
- **5–15 — baseline.** `create_agent.py`, then `run_session_1.py`. Read the session-1 answer out loud once, so you know what "before" sounds like.
- **15–25 — inspect and iterate.** `inspect_memory.py`. Is the memory tight and useful, or is it dumping whole documents? If it's noisy, the lever is the **memory protocol in the system prompt** (`create_agent.py`) — tighten it, re-run `create_agent.py` (idempotent), re-run session 1. Don't touch the data.
- **25–33 — the contradiction.** `run_session_2.py`. Confirm the answer *changed* and memory *updated* rather than appended.
- **33–37 — grade it.** `python check_memory.py`. It checks the session-2 answer + the store in ~2 seconds. A ✗ on "still routes to the retired workflow" means memory didn't override the stale fact — tighten the protocol in `create_agent.py` and re-run. This is the step that catches a demo that *looks* right but isn't.
- **37–40 — lock the demo.** Three terminals lined up, both answers ready to read.

Cut scope before you cut the demo: one clean two-session arc beats three half-finished stretch goals.

## Done when / Great when

**Done when:** session 2 answers the same question with the current policy, leads with what changed, and the prod-access entry was *updated* — not two conflicting copies sitting side by side. **`python check_memory.py` passes** (its scenario-agnostic floor plus any `acceptance.txt` you've set), and its advisory wired grade shows the retired workflow gone from the answer; `inspect_memory.py` shows you the store by eye.

**Great when:** the memory store is something you'd let a security team read — no dumped document text, dated entries, the re-org reflected in who owns what — and you can point at the exact `[memory: ...]` write in the session-1 stream where the agent decided a fact was worth keeping.

## The two-minute demo

Three terminals:
- **Left:** `outputs/session1.txt` — the January answer (Slack ticket, SRE pairing).
- **Right:** `outputs/session2.txt` — same question, sharper answer (self-serve cert, just-in-time access), leading with what changed.
- **Middle:** `python inspect_memory.py` — what the agent chose to remember, and that it *updated* rather than appended.

Read both answers out loud. Let the room hear the answer sharpen. Then name the one thing you'd harden before a client saw it — that's the practitioner version of the demo.

## What you walk out with

The artifact is the **diff plus the memory**:
- `outputs/session1.txt` → `outputs/session2.txt` — same question, the answer visibly corrected itself across sessions.
- `python inspect_memory.py --full` — the memory store the agent built and maintained on its own.

That pair is the whole pitch in thirty seconds: *"the agent gave a now-wrong answer the first time, learned the update, and never made the mistake again — and here's exactly what it chose to remember."*

## Make it your own

The mechanics don't change with the domain — an agent, a store, two sessions, a contradiction. Only the documents change. To re-point this at a scenario your clients will recognise, **swap the `synthetic-data/round1/` and `round2/` docs for your own** (nothing else is wired to onboarding), keep the round-1-vs-round-2 contradiction, and update the test question. These aren't shipped — you author the docs — but each is a five-minute reshape of the same exercise:

- **Customer Success.** Round 1: an enterprise account's history, contract summary, ticket log. Round 2: a new escalation, a contract amendment, a leadership change on the customer side. Question: *"Their new CTO just asked for a renewal proposal — what should we know going in?"* A better session-2 answer names the amendment and doesn't route to the contact who just left.
- **M&A Diligence.** Round 1: a target's financial summary, org chart, IP portfolio. Round 2: newly disclosed liabilities and a financial restatement that contradicts round 1. Question: *"What's your current risk assessment of this acquisition?"* A better answer flags the contradiction as a red flag and says so explicitly.
- **Sales Engineering.** Round 1: a customer's stack, their objections, the current pitch. Round 2: a new objection from the latest call and a competitive update. Question: *"Tomorrow's the final pitch — what's our strategy?"* A better answer anticipates the new objection instead of repeating the original plan.

Same store, same two-session loop. And when you swap the docs, write what a good session-2 answer looks like for the new domain into an `acceptance.txt` (one criterion per line — plain text, `/regex/`, or `!must-not`); `check_memory.py` then grades your build against your bar, not the onboarding one. If you want to scope memory per customer so Acme's facts never leak into Globex's answers, that's stretch goal S5.

## Stretch goals

Pick one after the core build — see [`stretch-goals.md`](./stretch-goals.md). The headline is the **Memory Curator** (`python stretch_memory_curator.py`): a second agent that gets the *same store* mounted and cleans it. Memory hygiene as a role, not a feature — the architecture maps straight onto how human teams keep institutional knowledge current. Where `check_memory.py` is the required rules-based *floor*, the Curator is the LLM *ceiling* — an actual second agent reasoning over the store, not a keyword scan.

## Rules of the data

Everything in `synthetic-data/` is fictional — the company, the people, the policies map to nothing real. The contradiction between round 1 and round 2 *is* the exercise, so don't edit the docs to smooth it over. Don't add real customer or firm data to the store.
