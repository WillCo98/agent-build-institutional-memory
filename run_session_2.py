"""
Session 2 — After memory + new context.

Same agent, same memory store, fresh session. Round2 docs contradict round1.
The agent should:
- Read memory first (its mount directory under `/mnt/memory/`)
- Notice the contradictions in the new docs
- UPDATE memory rather than appending
- Lead its answer with what changed and why

Usage:
    python run_session_2.py
"""

from pathlib import Path

from _common import create_session_or_explain, drive_session, get_client, memory_mount_path, read_id

# Match session 1
TEST_QUESTION = (
    "I just joined the company and I need read-only prod access to debug an "
    "issue tomorrow. What do I do? Be specific about the steps and the people "
    "I need to talk to."
)

DOCS_DIR = Path("synthetic-data/round2")
OUTPUT_DIR = Path("outputs")


def load_docs_as_context(docs_dir: Path) -> str:
    blocks = []
    for path in sorted(docs_dir.glob("*.md")):
        print(f"  including {path.name}")
        blocks.append(f"=====  DOCUMENT: {path.name}  =====\n{path.read_text()}")
    return "\n\n".join(blocks)


def main() -> None:
    client = get_client()

    hint = "Run create_agent.py first."
    agent_id = read_id(".agent_id", hint)
    environment_id = read_id(".environment_id", hint)
    memory_store_id = read_id(".memory_store_id", hint)

    print(f"Loading round2 docs from {DOCS_DIR}/...")
    context = load_docs_as_context(DOCS_DIR)

    print(f"\nStarting fresh session with same memory store {memory_store_id}...")
    session = create_session_or_explain(
        client,
        [".agent_id", ".environment_id", ".memory_store_id"],
        agent=agent_id,
        environment_id=environment_id,
        title="Session 2 — after memory + new context",
        resources=[
            {
                "type": "memory_store",
                "memory_store_id": memory_store_id,
                "access": "read_write",
                "instructions": (
                    "This is your persistent institutional memory. Some entries "
                    "may be out of date — reconcile against the new documents in "
                    "this session and UPDATE existing entries (don't just append)."
                ),
            }
        ],
    )
    # Stamp the session start so check_memory.py can tell whether outputs/session2.txt
    # came from THIS run or a stale earlier one (e.g. if the session errors below).
    Path(".last_session_id").write_text(session.id)

    memory_dir = memory_mount_path(session)  # e.g. /mnt/memory/institutional-memory

    user_message = (
        "I'm including some updated and new documents below. Some of them "
        "contradict things you learned in our previous session.\n\n"
        "Please:\n"
        f"1. First, check your memory store at {memory_dir}/ to see what you "
        "already know.\n"
        "2. Read the new documents below.\n"
        "3. Reconcile conflicts — UPDATE memory entries to reflect the "
        "newer information. Note dates.\n"
        "4. Answer the question.\n"
        "5. If your answer differs from your previous answer, lead with what "
        "changed and why.\n\n"
        f"{context}\n\n"
        "==================================================\n"
        f"QUESTION: {TEST_QUESTION}"
    )

    final_text_parts: list = []
    print("\nAgent working...\n")

    def on_event(event):
        if event.type == "agent.message":
            for block in event.content:
                if getattr(block, "type", None) == "text":
                    final_text_parts.append(block.text)
                    print(block.text, end="", flush=True)
        elif event.type == "agent.tool_use":
            name = getattr(event, "name", "?")
            inp = getattr(event, "input", {}) or {}
            target = inp.get("path") or inp.get("file_path") or inp.get("command") or ""
            if "/mnt/memory" in str(target):
                print(f"\n  [memory: {name}  {target}]", flush=True)
            else:
                print(f"\n  [{name}]", flush=True)

    drive_session(
        client,
        session,
        kickoff_events=[
            {
                "type": "user.message",
                "content": [{"type": "text", "text": user_message}],
            }
        ],
        on_event=on_event,
    )
    print("\n\n[agent finished]")

    final_text = "".join(final_text_parts)
    OUTPUT_DIR.mkdir(exist_ok=True)
    out = OUTPUT_DIR / "session2.txt"
    out.write_text(
        f"=== SESSION 2 ===\nQuestion: {TEST_QUESTION}\n\n--- ANSWER ---\n{final_text}\n",
        encoding="utf-8",
    )
    print(f"\nSaved to {out}")
    print(f"\nDiff outputs/session1.txt and outputs/session2.txt — the demo lives there.")
    print(f"Inspect updated memory:  python inspect_memory.py")
    print(f"Grade the arc (required):  python check_memory.py")


if __name__ == "__main__":
    main()
