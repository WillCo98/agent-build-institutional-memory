"""
List every memory in the agent's memory store, with content previews.

This is your demo helper — run it between sessions to see what the agent has
chosen to remember. Great for the live demo (three terminals: session 1
output, session 2 output, this).

Usage:
    python inspect_memory.py              # list with previews
    python inspect_memory.py --full       # full content of every memory
"""

import sys

import anthropic

from _common import get_client, read_id


def main() -> None:
    store_id = read_id(".memory_store_id", "Run create_agent.py first.")
    full = "--full" in sys.argv

    client = get_client()

    print(f"Memory store: {store_id}\n" + "=" * 60)

    # Iterating the list result auto-paginates (page.data would be page 1 only).
    # Sort client-side — the SDK's list() takes no order_by parameter.
    try:
        items = sorted(
            client.beta.memory_stores.memories.list(store_id, path_prefix="/"),
            key=lambda m: m.path,
        )
    except anthropic.APIStatusError as e:
        raise SystemExit(
            f"Could not read that memory store ({e}).\n"
            "Most likely .memory_store_id is stale (deleted, or another "
            "workspace). Delete it and re-run create_agent.py, or run "
            "`python check_setup.py` to validate all saved state."
        )
    if not items:
        print("(memory store is empty — has run_session_1.py been run?)")
        return

    for item in items:
        # `item.type` is "memory" for files, "memory_prefix" for directory nodes
        if item.type != "memory":
            print(f"\n[dir] {item.path}")
            continue

        retrieved = client.beta.memory_stores.memories.retrieve(
            item.id, memory_store_id=store_id
        )
        content = retrieved.content or ""

        print(f"\n--- {item.path}  ({len(content)} chars) ---")
        if full:
            print(content)
        else:
            preview = content[:400]
            print(preview + ("..." if len(content) > 400 else ""))


if __name__ == "__main__":
    main()
