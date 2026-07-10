# Troubleshooting

`check_setup.py` catches most of this before you build. Run it first, and again whenever something's off:

```bash
python check_setup.py
```

Everything below is a specific failure and its fix. You shouldn't need to flag anyone down — that's the point.

---

## "It won't take my API key" / auth errors

**Symptom:** `check_setup.py` says the key was rejected, or a script exits asking for a key.

**Fix:** the scripts read your key from a gitignored `.env` at the repo root (created from a template the first time you run anything), or from an `ANTHROPIC_API_KEY` shell variable — the shell variable wins if both are set. Open `.env`, paste the **whole** key after `ANTHROPIC_API_KEY=` (no quotes, no spaces; it starts with `sk-ant-`), save, and re-run `check_setup.py`. It has to be a **workspace** API key from the Console, not a personal one — memory stores live in a workspace. Once you see `✓ API key verified — any error after this is not the API key`, stop debugging the key.

A connection or proxy error (as opposed to a *rejected* key) is a network problem, not a key problem — see [`SETUP.md`](./SETUP.md) for the proxy flow.

---

## State files: what each one is, and when to delete it

The scripts save the IDs of the cloud resources they create into dot-files at the repo root, so the next script can find them. They're gitignored. You rarely touch them by hand — but when a saved ID goes stale, deleting the right one is the fix.

| File | Written by | Points at | Delete it when… |
| --- | --- | --- | --- |
| `.agent_id` | `create_agent.py` | your memory agent | the agent was deleted, or you want a fresh one |
| `.environment_id` | `create_agent.py` | the cloud container sessions run in | the environment was deleted |
| `.memory_store_id` | `create_agent.py` | the persistent memory store | you want a clean store for a fresh demo arc |
| `.curator_agent_id` | `stretch_memory_curator.py` | the curator sub-agent (stretch goal) | the curator was deleted |

Deleting a dot-file just makes the next `create_agent.py` (or `stretch_memory_curator.py`) create a fresh resource and re-save the ID. It never touches the remote resource.

**The one-shot reset:**

```bash
python check_setup.py --reset
```

This deletes **all** the local state files above — and nothing remote. Use it when several IDs are stale, or when you want the clean two-session demo from scratch. After a reset, run `create_agent.py` again.

---

## "A saved ID points at a resource this key can't see"

**Symptom:** a script exits with roughly that line, or `check_setup.py` flags a saved ID with a `✗`.

**What's happening:** a dot-file holds an ID your current key can't reach — usually because the resource was deleted, or the dot-file was created with a key from a *different* workspace (classic on a shared team workspace, or after you switch keys).

**Fix:** delete the flagged dot-file and re-run `create_agent.py`, or just `python check_setup.py --reset` to clear all of them at once. `check_setup.py` tells you which specific file is stale.

---

## The session looks hung

**Symptom:** a `run_session_*.py` script sits there with no new output.

**What's happening:** managed-agent sessions run **server-side**. A quiet terminal usually means the agent is thinking or running a long tool call, not that anything crashed. After a while the script prints a "still running" reminder with the URL.

**Fix:** open the **Console trace URL the script printed at the top** (`Watch it live: …`) and watch the session live. If it's genuinely stuck, **Ctrl-C is safe** — the session keeps running on the server; you're only detaching your terminal. You can re-open the Console URL any time, and once the session finishes you can read the answer there. (If the URL 404s, swap `default` in it for your workspace ID — the script prints that caveat too.)

---

## Session 1 wrote nothing / the store looks empty

**Symptom:** `inspect_memory.py` prints `(memory store is empty…)` after session 1.

**What's happening:** the agent answered but never wrote to `/mnt/memory/` — so session 2 has nothing to improve on.

**Fix:** re-read the session-1 stream. Did any `[memory: …]` lines appear? If not, the agent didn't save anything, and the lever is the **memory protocol in the system prompt** (`create_agent.py`) — that's what tells the agent to record what it learns. Tighten that instruction, re-run `create_agent.py` (idempotent), and re-run session 1. Don't go looking for the fix in the data or the run scripts.

---

## Session 2 isn't any sharper

**Symptom:** session 2's answer matches session 1's, or ignores the round-2 contradiction.

**What's happening:** one of two things — the agent didn't *read* memory at the start of session 2, or memory never held the round-1 facts to begin with.

**Fix:** run `python inspect_memory.py` **between** the two sessions. If the store is empty or thin after session 1, this is really the "session 1 wrote nothing" problem above — fix that first. If the store is healthy but session 2 still ignores it, tighten the "check memory first" and "lead with the contradiction" instructions in the system prompt, then re-run. The store is the evidence; check it before you change anything.

---

## The baseline demo falls flat (the store wasn't empty)

**Symptom:** `check_setup.py` warns that the memory store already has memories but session 1 hasn't run here yet; or session 1's "baseline" answer is already sharp, leaving nothing for session 2 to improve.

**What's happening:** you're reusing a store a previous run already filled. Session 1 is supposed to start from an **empty** store — that's what makes it a believable "before."

**Fix:**

```bash
python check_setup.py --reset
python create_agent.py
```

That gives you a fresh store and a genuine baseline. Then run the two sessions in order.

---

## "Environment already exists" on a shared workspace

**Symptom:** you expect a 409 when several people run `create_agent.py` against the same team workspace.

**What's happening:** nothing you need to handle. Environment names are unique per workspace, so `create_agent.py` **gets-or-creates** by name (`memory-agent-env`) instead of blindly creating — the second person to run it reuses the first one's environment rather than hitting a 409. Agents and stores are reused via the dot-files. Re-running any create script is safe by design.

---

## Still stuck?

Re-run `python check_setup.py` and read the message — it prints a specific next step, not a raw traceback. If it points you at [`SETUP.md`](./SETUP.md), the venv path there clears the large majority of laptop-specific problems.
