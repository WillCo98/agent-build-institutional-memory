"""
Provision the three things this track needs:
  1. A Managed Agent with the full agent toolset
  2. A cloud Environment (the container the agent runs in)
  3. A Memory Store that survives across sessions

The memory store mounts at /mnt/memory/<store-name-slug>/ inside the session
container — /mnt/memory/institutional-memory/ for this store's name. The run
scripts read the exact path from the session's resources (mount_path) and
inject it into the kickoff message. The agent reads and writes it with normal
file tools. It persists across sessions — that's the whole point of this track.

IDs are saved to .agent_id, .environment_id, .memory_store_id so the
run_session_* scripts can pick them up.

Usage:
    export ANTHROPIC_API_KEY="sk-ant-..."
    python create_agent.py
"""

from pathlib import Path

import anthropic

from _common import get_client


SYSTEM_PROMPT = """\
You are the Institutional Memory Agent for a fast-growing company.

Your job: be the smartest possible answer to questions about how this company
works — its policies, its people, its customers, its product. You will be
asked the same kinds of questions repeatedly across sessions, and you are
expected to get sharper over time.

# Memory protocol (mandatory)

You have a persistent memory store mounted as a directory under `/mnt/memory/`
— the exact mount directory is named in your memory-store mount note and in
the user's message. It survives across sessions. Treat it like the team wiki.
Only files inside that mount directory are saved to the store; anything
written elsewhere under `/mnt/memory/` is silently lost when the session ends.

1. **At the start of EVERY session**, list and skim your memory mount
   directory before doing anything else. Use your bash and file tools.
2. Read any files that look relevant to the current question.
3. As you work, **record what you learn for future sessions**:
   - Policies (especially anything with a date or version)
   - Key people in named roles
   - Customer-specific facts
   - Recurring questions and your best answer
4. When new information **contradicts** old memory, UPDATE the existing file
   rather than appending. Note the effective date. Trust the newer version.
5. Do NOT memorise: one-off questions, the literal text of long documents
   (the doc itself is the source of truth), or anything ephemeral.

# How to answer

- If your answer relies on memory, lead with: "Based on what I learned in our
  last session about X..."
- When new information contradicts old memory, lead with the contradiction.
  Don't paper over it.
- Be concise.
"""


def main() -> None:
    client = get_client()

    # Re-running this script must not duplicate resources: agents and memory
    # stores are reused via their saved ID files, and environments are looked
    # up by name (environment names are unique per workspace — a second bare
    # create returns 409, which bites on shared team workspaces).

    # 1. Agent — create it, or UPDATE it in place on reuse. The reuse path must
    #    re-push the config: a retrieve-only branch silently ignores an edited
    #    SYSTEM_PROMPT/model (the whole point of this exercise is editing the
    #    prompt, so "edit, re-run create_agent.py" has to actually apply). Same
    #    pattern the swarm's create_coordinator.py already uses.
    agent_config = dict(
        model="claude-sonnet-5",
        system=SYSTEM_PROMPT,
        tools=[{"type": "agent_toolset_20260401"}],
    )
    if Path(".agent_id").exists():
        agent_id = Path(".agent_id").read_text().strip()
        try:
            current = client.beta.agents.retrieve(agent_id)
        except anthropic.APIStatusError:
            raise SystemExit(
                f"Saved .agent_id ({agent_id[:18]}…) is unreachable with this key "
                "(deleted, or another workspace). Delete .agent_id and re-run — "
                "or run `python check_setup.py` to validate all saved state."
            )
        client.beta.agents.update(agent_id, version=current.version, **agent_config)
        print(f"Agent updated (re-pushed prompt/model): {agent_id}")
    else:
        agent = client.beta.agents.create(
            name="Institutional Memory Agent",
            metadata={"hackathon": "partner-basecamp-2026", "track": "memory-agent"},
            **agent_config,
        )
        Path(".agent_id").write_text(agent.id)
        print(f"Agent created:        {agent.id}")

    # 2. Environment (the cloud container) — get-or-create by name
    env_name = "memory-agent-env"
    environment = next(
        (e for e in client.beta.environments.list() if e.name == env_name), None
    )
    if environment is not None:
        print(f"Reusing environment:  {environment.id}")
    else:
        environment = client.beta.environments.create(
            name=env_name,
            config={
                "type": "cloud",
                "networking": {"type": "unrestricted"},
            },
        )
        print(f"Environment created:  {environment.id}")
    Path(".environment_id").write_text(environment.id)

    # 3. Memory store — the thing that persists across sessions
    if Path(".memory_store_id").exists():
        store_id = Path(".memory_store_id").read_text().strip()
        print(f"Reusing memory store: {store_id}")
    else:
        memory_store = client.beta.memory_stores.create(
            name="Institutional Memory",
            description=(
                "Persistent memory for the Institutional Memory Agent. Contains "
                "policies, key people, customer facts, and recurring Q&A learned "
                "across sessions. Used as authoritative wiki — newer entries "
                "supersede older ones on the same topic."
            ),
        )
        Path(".memory_store_id").write_text(memory_store.id)
        print(f"Memory store created: {memory_store.id}")
    store_id = Path(".memory_store_id").read_text().strip()

    print("\nSetup complete.")
    print(f"  Inspect the memory store in the Console (Memory Stores):")
    print(f"    store id {store_id}")
    print(f"  Or programmatically with:  python inspect_memory.py")
    print(f"\nNext:  python run_session_1.py")


if __name__ == "__main__":
    main()
