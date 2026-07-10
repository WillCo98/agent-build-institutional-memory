"""
Stretch goal: the Memory Curator sub-agent.

After multiple sessions, the main agent's memory store can become messy —
duplicates, stale facts, contradictions that were never resolved.

This script creates a SECOND agent whose only job is to curate memory:
- Read the main agent's memory store (mounted read/write in ITS session)
- Merge duplicates
- Flag unresolved contradictions
- Prune anything that's no longer load-bearing

The trick that makes this work: the curator doesn't get "access to another
agent" — it gets the same MEMORY STORE mounted into its own session. Memory
belongs to the store, not the agent. Any agent you attach the store to can
read and curate it.

In a real system, you'd run this on a schedule (a scheduled deployment /
Routine).

Usage:
    python stretch_memory_curator.py     (run after at least one session)
"""

import os
from pathlib import Path

from anthropic import Anthropic


CURATOR_SYSTEM_PROMPT = """\
You are the Memory Curator. Your only job is memory hygiene.

Another agent's memory store is mounted at /mnt/memory/ in your session
(read/write). On each run:

1. List every entry in the store.
2. Merge any duplicates — keep the most recent version, fold the others in.
3. Flag any unresolved contradictions to the operator with a short summary.
4. Prune anything that is:
   - Ephemeral (one-off support tickets, individual conversation snippets)
   - Subsumed by a more general entry that was added later
5. Produce a one-paragraph summary of what you did.

Do NOT add new knowledge. Do NOT answer domain questions. You only clean.
"""


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    for required in (".environment_id", ".memory_store_id"):
        if not Path(required).exists():
            raise SystemExit(f"Missing {required}. Run create_agent.py first.")

    environment_id = Path(".environment_id").read_text().strip()
    memory_store_id = Path(".memory_store_id").read_text().strip()

    client = Anthropic()

    # Create the curator agent once; reuse it on later runs
    curator_path = Path(".curator_agent_id")
    if curator_path.exists():
        curator_id = curator_path.read_text().strip()
        print(f"Reusing curator agent {curator_id}")
    else:
        curator = client.beta.agents.create(
            name="Memory Curator",
            model="claude-haiku-4-5",  # Fast, cheap, sufficient for housekeeping
            system=CURATOR_SYSTEM_PROMPT,
            tools=[{"type": "agent_toolset_20260401"}],
            metadata={
                "role": "memory-curator",
                "hackathon": "partner-basecamp-2026",
            },
        )
        curator_id = curator.id
        curator_path.write_text(curator_id)
        print(f"Curator agent created: {curator_id}")

    # The curator gets its own session with the SAME memory store attached —
    # sessions require an environment, and the store must be a session
    # resource or the curator has nothing to curate.
    session = client.beta.sessions.create(
        agent=curator_id,
        environment_id=environment_id,
        title="Memory curation pass",
        resources=[
            {
                "type": "memory_store",
                "memory_store_id": memory_store_id,
                "access": "read_write",
                "instructions": (
                    "This is the memory store you curate. Mounted at "
                    "/mnt/memory/. Clean it per your standard process."
                ),
            }
        ],
    )

    print("Curator working...\n")
    text_parts: list[str] = []
    with client.beta.sessions.events.stream(session.id) as stream:
        client.beta.sessions.events.send(
            session.id,
            events=[
                {
                    "type": "user.message",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Run a curation pass on the memory store "
                                "mounted at /mnt/memory/. Follow your standard "
                                "process. Report back when done."
                            ),
                        }
                    ],
                }
            ],
        )
        for event in stream:
            if event.type == "agent.message":
                for block in event.content:
                    if getattr(block, "type", None) == "text":
                        text_parts.append(block.text)
            elif event.type == "agent.tool_use":
                name = getattr(event, "name", "?")
                print(f"  [{name}]", flush=True)
            elif event.type == "session.status_idle":
                break

    print("\n=== CURATOR REPORT ===")
    print("".join(text_parts) or "(no text returned — check the session in the Console)")
    print("\nSee what changed:  python inspect_memory.py")


if __name__ == "__main__":
    main()
