"""
Verify the memory arc — run this AFTER run_session_2.py.

The habit this enforces: "session 2 felt sharper" is not the same as "memory did
its job." Before you demo, you check the session-2 answer (and the store) against
acceptance criteria. This is that check — deliberately dumb: no grading model, just
a fast local read of outputs/session2.txt plus the memory store the agent built.

It is built NOT to box you in. Three layers, loosest to tightest:

  • THE FLOOR (always gates, scenario-agnostic): session 2 exists and has real
    content. True for the wired onboarding scenario or any domain you swap in. A
    custom build can never hard-fail just for being custom.

  • YOUR CRITERIA (gates, only if you write them): drop an `acceptance.txt` next to
    this script — one criterion per line, checked against the session-2 answer — and
    the check grades YOUR scenario against YOUR bar. Format at the bottom of this file.

  • THE WIRED GRADE (advisory, only for the shipped onboarding scenario): if round2
    still carries the shipped contradiction, you also get the "Done when" bar graded
    for free — the retired workflow is gone from the answer, the current policy is
    cited, and the store looks updated-not-appended. Keyword heuristics on prose;
    a ✗ means "go look," not "you failed." They never gate, and they go quiet the
    moment you adapt the scenario.

Reading the store needs your key + .memory_store_id (same as inspect_memory.py). If
that isn't reachable, the answer checks still run; the store hygiene note is skipped.

Usage:
    python check_memory.py
"""

import re
import sys
from pathlib import Path

# Windows consoles default to cp1252; the ✓ / ✗ output below crashes on a plain
# print when stdout isn't UTF-8 (a legacy console, or stdout redirected to a
# file). This grader imports _common only lazily (when it reads the store), so
# its early floor/answer prints run before that guard — it carries its own here.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

SESSION2 = Path("outputs/session2.txt")
ACCEPTANCE = Path("acceptance.txt")
WIRED_ROUND2 = Path("synthetic-data/round2")

# --- wired-scenario reference (only used when the shipped contradiction is intact) ---
RETIRED_MARKERS = [
    "#sre-access-requests", "sre-access-requests", "sre access request",
    "sre pairing", "pairing session",
]
NEW_POLICY_MARKERS = [
    "self-serve", "self serve", "self-service", "certification", "certif",
    "just-in-time", "just in time", "jit", "2026-05-15", "may 2026", "may 15",
]
CHANGE_MARKERS = [
    "changed", "no longer", "previously", "used to", "update", "since",
    "as of", "new policy", "replaced", "superseded",
]
DEPRECATION_MARKERS = [
    "retired", "deprecated", "no longer", "old ", "former", "superseded",
    "replaced", "historical", "until 2026-05", "before ", "previously",
]

# Negation words that, near a retired marker, mean the answer is naming the old
# path only to say it's GONE (correct) rather than recommending it (the failure).
NEGATION_NEAR = [
    "no ", "not ", "no longer", "eliminat", "remov", "retired", "was ", "were ",
    "used to", "instead", "replac", "anymore", "don't", "do not", "deprecat",
    "gone", "former", "previously", "old ", "superseded", "phased out",
]


def _has(text_lc, *needles):
    return any(n.lower() in text_lc for n in needles)


def _staleness_warning(output_path):
    """If .last_session_id (stamped when the session starts) is newer than the
    output file, the most recent run didn't write this file — it probably errored
    (e.g. a transient 'API overloaded') before saving. Grading a leftover file
    from an earlier run would report a misleading PASS, so flag it."""
    marker = Path(".last_session_id")
    try:
        if marker.exists() and output_path.exists():
            if marker.stat().st_mtime > output_path.stat().st_mtime + 2:
                return (f"⚠ STALE: {output_path} is older than your last session — "
                        "the latest run may have errored before writing it. "
                        "Re-run run_session_2.py to grade THIS session.")
    except OSError:
        pass
    return None


def _retired_recommended(text_lc):
    """Retired markers that appear WITHOUT negation nearby — i.e. still being
    recommended. A correct session-2 answer names the retired path only to say
    it was removed ("no SRE pairing session anymore"); that negated context must
    NOT be flagged as routing to it. Only an un-negated mention is the failure."""
    hits = []
    for m in RETIRED_MARKERS:
        ml, start = m.lower(), 0
        while True:
            i = text_lc.find(ml, start)
            if i < 0:
                break
            window = text_lc[max(0, i - 90):i + len(ml) + 40]
            if not any(n in window for n in NEGATION_NEAR):
                hits.append(m)
                break
            start = i + len(ml)
    return hits


def _found(text_lc, needles):
    return [n for n in needles if n.lower() in text_lc]


def load_criteria():
    """Parse acceptance.txt, or None if not written. One criterion per line;
    blank/#-comment lines ignored.
      plain text  -> the answer MUST contain it (case-insensitive)
      /regex/     -> the answer MUST match this regex (case-insensitive)
      leading "!" -> negate: e.g. "!acquire" or "!/re/" means MUST NOT contain / match
    """
    if not ACCEPTANCE.exists():
        return None
    crits = []
    for raw in ACCEPTANCE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        negate = line.startswith("!")
        if negate:
            line = line[1:].strip()
        is_regex = len(line) >= 2 and line.startswith("/") and line.endswith("/")
        pattern = line[1:-1] if is_regex else line
        crits.append({"raw": raw.strip(), "negate": negate, "regex": is_regex, "pattern": pattern})
    return crits


def check_criterion(text, text_lc, c):
    if c["regex"]:
        try:
            found = re.search(c["pattern"], text, re.IGNORECASE) is not None
        except re.error as e:
            return None, f"bad regex: {e}"
    else:
        found = c["pattern"].lower() in text_lc
    return ((not found) if c["negate"] else found), None


def is_wired_scenario() -> bool:
    """True only if round2 still carries the shipped contradiction — i.e. you
    haven't swapped synthetic-data/ for your own domain."""
    try:
        if not WIRED_ROUND2.is_dir():
            return False
        blob = " ".join(p.read_text(errors="ignore").lower()
                        for p in WIRED_ROUND2.glob("*.md"))
        return "2026-05-15" in blob or "#sre-access-requests" in blob
    except OSError:
        return False


def read_memory_items():
    """[(path, content)] from the store, or None if unreachable."""
    try:
        from _common import get_client
    except Exception:
        return None
    store_path = Path(".memory_store_id")
    if not store_path.exists():
        return None
    store_id = store_path.read_text().strip()
    try:
        client = get_client()
        items = list(client.beta.memory_stores.memories.list(store_id, path_prefix="/"))
    except Exception:
        return None
    out = []
    for item in items:
        if getattr(item, "type", None) != "memory":
            continue
        try:
            r = client.beta.memory_stores.memories.retrieve(item.id, memory_store_id=store_id)
            out.append((item.path, r.content or ""))
        except Exception:
            out.append((item.path, ""))
    return out


def main() -> None:
    # ── THE FLOOR (scenario-agnostic, gates) ─────────────────────────────────
    if not SESSION2.exists():
        raise SystemExit(
            f"✗ No {SESSION2}\n"
            "  Run `python run_session_2.py` first — there's no answer to check yet."
        )
    answer = SESSION2.read_text(encoding="utf-8")
    answer_lc = answer.lower()
    if len(answer.strip()) < 120:
        raise SystemExit(
            f"✗ {SESSION2} exists but is nearly empty ({len(answer.strip())} chars).\n"
            "  The session likely errored before answering — open the Console trace."
        )

    stale = _staleness_warning(SESSION2)
    print(f"Checking {SESSION2}  ({len(answer.strip())} chars)\n")
    print("FLOOR — is there a real session-2 answer?")
    print("  ✓ Exists and has content")
    if stale:
        print(f"  {stale}")

    # FLOOR — memory must have actually PERSISTED, not just produced an answer.
    # The session-2 answer is derivable from the in-context round-2 docs, so
    # grading it alone can't tell "memory worked" from "memory silently failed."
    # A memory exercise with an empty store after session 2 has FAILED (classic
    # cause: a mount-path mismatch — the store mounts at /mnt/memory/<store-name>/,
    # not /mnt/memory/). Only gates when the store is reachable.
    store_items = read_memory_items()
    if store_items is not None and len(store_items) == 0:
        raise SystemExit(
            "✗ The memory store is EMPTY after session 2 — nothing persisted.\n"
            "  Cross-session memory silently failed (the agent wrote outside the real\n"
            "  mount, or never wrote). Check that the mount path in create_agent.py's\n"
            "  system prompt and the resource `instructions` in run_session_*.py match\n"
            "  where the store actually mounts, then re-run create_agent.py + both sessions."
        )
    if store_items:
        print(f"  ✓ Memory store persisted {len(store_items)} file(s)")
    elif store_items is None:
        print("  · (store not reachable from here — skipping the persistence check)")
    print()

    gate_failures = 0

    # ── YOUR CRITERIA (gates, only if acceptance.txt exists) ─────────────────
    criteria = load_criteria()
    if criteria is not None:
        print(f"YOUR CRITERIA — from acceptance.txt ({len(criteria)} defined):")
        if not criteria:
            print("  (acceptance.txt is present but empty — add one criterion per line)")
        for c in criteria:
            ok, err = check_criterion(answer, answer_lc, c)
            if err:
                print(f"  ⚠ {c['raw']}   ({err})")
                continue
            kind = "must NOT contain" if c["negate"] else "must contain"
            print(f"  {'✓' if ok else '✗'} [{kind}] {c['raw']}")
            if not ok:
                gate_failures += 1
        print()

    # ── THE WIRED GRADE (advisory, only for the shipped onboarding scenario) ──
    if is_wired_scenario():
        print("WIRED GRADE — the onboarding 'Done when' bar (advisory, no gate):")
        recommended = _retired_recommended(answer_lc)
        mentioned = _found(answer_lc, RETIRED_MARKERS)
        if recommended:
            print(f"  ✗ Still routes to the RETIRED workflow: {', '.join(recommended)} — "
                  "memory didn't override the stale fact.")
        elif mentioned:
            print(f"  ✓ Names the retired workflow only to say it's gone "
                  f"({', '.join(mentioned)}) — that's the right move, not a miss.")
        else:
            print("  ✓ Does NOT send the new hire down the retired path")
        new_hits = _found(answer_lc, NEW_POLICY_MARKERS)
        if new_hits:
            print(f"  ✓ Cites the current (May) policy: {', '.join(sorted(set(new_hits)))}")
        else:
            print("  ✗ Doesn't cite the current policy (self-serve certification + "
                  "just-in-time IAM access, effective 2026-05-15).")
        if _has(answer_lc, *CHANGE_MARKERS):
            print("  ✓ Leads with / signals what changed")
        else:
            print("  ✗ Doesn't frame the answer around what changed since last time.")

        items = read_memory_items()
        if items is None:
            print("  · store hygiene: skipped (couldn't read the store — run check_setup.py)")
        elif not items:
            print("  · store hygiene: the store is empty — has run_session_1.py run?")
        else:
            stale, access_entries = [], 0
            for path, content in items:
                c_lc = content.lower()
                if _has(c_lc, *RETIRED_MARKERS) and not _has(c_lc, *DEPRECATION_MARKERS):
                    stale.append(path)
                if _has(c_lc, "prod access", "production access", "read-only prod",
                        "read only prod", "iam", "prod-access"):
                    access_entries += 1
            if stale:
                print(f"  ✗ store hygiene: retired workflow stored as current in "
                      f"{', '.join(stale)} — that's an append, not an update.")
            else:
                print("  ✓ store hygiene: no retired workflow sitting in memory as current")
            if access_entries >= 2:
                print(f"  ⚠ store hygiene: {access_entries} prod-access entries — check "
                      "inspect_memory.py that they were reconciled into one, not duplicated.")
        print("  (Advisory only — the lever is the memory protocol in create_agent.py, "
              "never the data.)")
        print()
    elif criteria is None:
        print("ADAPTED SCENARIO — the wired onboarding checks don't apply to your build.")
        print("  Define what a good session-2 answer looks like for YOUR domain:")
        print("  create acceptance.txt next to this script, one criterion per line, e.g.:")
        print("      # M&A diligence variant")
        print("      /restatement|contradict/    # must flag the new liability")
        print("      !acquire without conditions  # must NOT ignore the red flag")
        print("  Then re-run — the check grades your build against your bar.")
        print()

    # ── VERDICT ──────────────────────────────────────────────────────────────
    if gate_failures:
        raise SystemExit(
            f"✗ {gate_failures} of your acceptance criteria failed. The lever is the "
            "memory protocol in create_agent.py's system prompt (check memory first, "
            "update-don't-append, prefer the newer dated fact) — tighten it, re-run "
            "create_agent.py, then both sessions. Never edit the data."
        )
    print("✓ PASSED — a real session-2 answer, and it meets the bar in play.")
    if stale:
        print("  ⚠ ...but you graded a STALE file — re-run run_session_2.py to grade THIS session.")
    if criteria is None and is_wired_scenario():
        print("  (Read the advisory WIRED GRADE above — especially the retired-path line.)")


if __name__ == "__main__":
    main()
