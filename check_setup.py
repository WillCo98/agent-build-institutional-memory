"""
Run this FIRST — before anything else in this repo.

It verifies, in order:
  1. Dependencies (installs the anthropic SDK if missing — survives locked-down Pythons)
  2. Your API key (.env or shell variable), with a live 1-token ping
  3. The SDK is new enough for Managed Agents memory stores
  4. Any saved resource IDs from earlier runs still point at real resources
  5. That your memory store is empty BEFORE session 1 — the demo arc depends on it

Usage:
    python check_setup.py            # run all checks
    python check_setup.py --reset    # delete LOCAL state files (never remote resources)
"""

# ── 1. Dependencies — safe to re-run; survives PEP 668 / no-admin Pythons ──
import importlib.util, subprocess, sys


def _ensure_packages(requirements):
    """requirements: list of (import_name, pip_spec). Install only what is missing,
    into the running interpreter. Tries a normal install, then user-space, then a
    PEP 668 override. Pip output is captured, not streamed; only if every strategy
    fails does it surface the reason, with the venv fix instead of a traceback."""
    missing = [pip for mod, pip in requirements if importlib.util.find_spec(mod) is None]
    if not missing:
        return
    print("Installing " + ", ".join(missing) + " — first run only, please wait…", flush=True)
    base = [sys.executable, "-m", "pip", "install", "-q"]
    last = None
    for extra in ([], ["--user"], ["--user", "--break-system-packages"], ["--break-system-packages"]):
        last = subprocess.run(base + extra + missing, capture_output=True, text=True)
        if last.returncode == 0:
            return
    pip_said = (last.stderr or last.stdout or "").strip().splitlines() if last else []
    tail = "\n      ".join(pip_said[-3:]) if pip_said else "(no output from pip)"
    raise SystemExit(
        "\n  Couldn't install: " + ", ".join(missing) + "\n"
        "  This Python is locked down (PEP 668) or offline. Quickest fix is a venv:\n"
        f"      {sys.executable} -m venv .venv\n"
        "      source .venv/bin/activate          # Windows: see SETUP.md\n"
        f"      pip install {' '.join(missing)}\n"
        "  Corporate proxy or PyPI blocked? See SETUP.md in the repo root.\n"
        f"  (pip said: {tail})\n"
    )


_ensure_packages([("anthropic", "anthropic")])
print("✓ Dependencies ready")

from pathlib import Path

STATE_FILES = [
    ".agent_id",
    ".environment_id",
    ".memory_store_id",
    ".curator_agent_id",
]


def do_reset():
    removed = []
    for f in STATE_FILES:
        p = Path(f)
        if p.exists():
            p.unlink()
            removed.append(f)
    if removed:
        print("Removed local state files: " + ", ".join(removed))
        print("(Remote agents/environments/stores are untouched — the next "
              "create_agent.py run reuses or recreates what it needs.)")
    else:
        print("No local state files to remove.")


def main():
    if "--reset" in sys.argv:
        do_reset()
        return

    import anthropic
    from _common import get_client, load_env

    failures = 0

    # ── 2. API key + live ping ──
    key = load_env()
    ping = anthropic.Anthropic(api_key=key, timeout=30.0, max_retries=1)
    try:
        ping.messages.create(
            model="claude-haiku-4-5", max_tokens=1,
            messages=[{"role": "user", "content": "ping"}],
        )
    except anthropic.AuthenticationError:
        raise SystemExit(
            "✗ That key was rejected. Open .env and paste the whole key "
            "(it starts with sk-ant-), then re-run."
        )
    except Exception as exc:
        raise SystemExit(
            f"✗ Could not reach the Claude API ({type(exc).__name__}). "
            "Check your connection / proxy (SETUP.md), then re-run."
        )
    print("✓ API key verified — any error after this is not the API key")

    client = get_client()

    # ── 3. SDK surfaces (memory stores are the one this track lives on) ──
    needed = ("agents", "sessions", "environments", "memory_stores")
    missing = [s for s in needed if not hasattr(client.beta, s)]
    if missing:
        raise SystemExit(
            f"✗ Your anthropic SDK ({anthropic.__version__}) is too old — "
            f"missing client.beta.{missing[0]}.\n"
            "  Fix: pip install -U 'anthropic>=0.116.0'"
        )
    # Zero-write probe that the workspace can use Managed Agents at all
    try:
        next(iter(client.beta.memory_stores.list()), None)
    except Exception as e:
        failures += 1
        print("✗ Could not list memory stores with this key.")
        print(f"    API said: {e}")
        print("    Is this a workspace API key from the Console?")
    else:
        print(f"✓ SDK + workspace can use Managed Agents memory stores "
              f"(anthropic {anthropic.__version__})")

    # ── 4. Saved state from earlier runs ──
    def check_id(label, retrieve, res_id, fix):
        nonlocal failures
        try:
            return retrieve(res_id)
        except Exception:
            failures += 1
            print(f"✗ {label} points at a resource this key can't see ({res_id[:18]}…).")
            print(f"    Fix: {fix}  (or `python check_setup.py --reset` to clear all local state)")
            return None

    store = None
    if Path(".agent_id").exists():
        if check_id("Saved agent", lambda i: client.beta.agents.retrieve(i),
                    Path(".agent_id").read_text().strip(),
                    "delete .agent_id and re-run create_agent.py"):
            print("✓ Saved agent is reachable")
    if Path(".environment_id").exists():
        if check_id("Saved environment", lambda i: client.beta.environments.retrieve(i),
                    Path(".environment_id").read_text().strip(),
                    "delete .environment_id and re-run create_agent.py"):
            print("✓ Saved environment is reachable")
    if Path(".memory_store_id").exists():
        store = check_id("Saved memory store", lambda i: client.beta.memory_stores.retrieve(i),
                         Path(".memory_store_id").read_text().strip(),
                         "delete .memory_store_id and re-run create_agent.py")
        if store:
            print("✓ Saved memory store is reachable")
    if Path(".curator_agent_id").exists():
        if check_id("Saved curator", lambda i: client.beta.agents.retrieve(i),
                    Path(".curator_agent_id").read_text().strip(),
                    "delete .curator_agent_id and re-run stretch_memory_curator.py"):
            print("✓ Saved curator agent is reachable")

    # ── 5. The demo-arc check: session 1 needs an EMPTY store ──
    if store is not None and not Path("outputs/session1.txt").exists():
        store_id = Path(".memory_store_id").read_text().strip()
        try:
            has_memories = next(
                iter(client.beta.memory_stores.memories.list(store_id, path_prefix="/")), None
            ) is not None
        except Exception:
            has_memories = False
        if has_memories:
            print("! Heads-up: this memory store already has memories, but session 1 "
                  "hasn't run here yet.")
            print("    Your 'baseline' answer won't look like a baseline. For the clean "
                  "two-session demo arc:")
            print("    python check_setup.py --reset   (then re-run create_agent.py — "
                  "you'll get a fresh store)")

    print()
    if failures:
        raise SystemExit(f"{failures} check(s) failed — fix the ✗ items above, then re-run.")
    print("All checks passed. Build order: create_agent.py → run_session_1.py "
          "→ inspect_memory.py → run_session_2.py")


if __name__ == "__main__":
    main()
