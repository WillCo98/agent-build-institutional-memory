# Setup & Troubleshooting

One page to get any laptop — including a locked-down corporate one — running this repo's scripts. **The fastest reliable path is a virtual environment.** Everything here is plain Python; there are no notebooks.

---

## The 4-command setup (do this once)

```bash
python3 -m venv .venv                 # create an isolated environment
source .venv/bin/activate             # macOS/Linux  (Windows: .venv\Scripts\activate)
pip install -r requirements.txt       # install the anthropic SDK
python check_setup.py                 # verify deps, key, SDK, and memory-store access
```

`check_setup.py` is the gate for the whole repo — when it prints **All checks passed**, you're ready to build (start with [`BRIEF.md`](./BRIEF.md)). On its first run it creates a gitignored `.env` for your API key; see "API key" below.

> You don't strictly need the venv — `check_setup.py` installs the SDK on its own if it's missing — but a venv is the one setup that sidesteps *every* problem below at once.

---

## Common problems

### `error: externally-managed-environment` (PEP 668)
**Why:** you're installing into a system Python (Homebrew on macOS, or the OS Python on Debian/Ubuntu) that's marked off-limits for `pip`. **Fix:** usually nothing — `check_setup.py` detects a locked-down Python and falls back to a user-space install automatically on the **first** run, printing just `✓ Dependencies ready`. Prefer not to touch the system Python at all? Use the venv above; it's the cleanest path. You'll only get an error if **every** install strategy fails — an offline machine or a blocked PyPI (see the proxy section below).

### No admin rights / `permission denied` on install
A venv is owned by you, so it needs no admin rights — use it. If you can't make one, `check_setup.py`'s automatic `--user` fallback installs into your home directory instead.

### Corporate proxy / PyPI blocked by the firewall
Point pip at your proxy, then install:

```bash
export HTTPS_PROXY=http://user:pass@proxy.company.com:8080
export HTTP_PROXY=$HTTPS_PROXY
pip install -r requirements.txt
```

If PyPI itself is blocked, ask IT for your internal package mirror and use it:
`pip install -r requirements.txt --index-url https://<your-mirror>/simple`.

### "I don't have Python" / wrong version
You need **Python 3.9 or newer**. Install from [python.org](https://www.python.org/downloads/) or your company's software portal, then re-open your terminal so it's detected. Check with `python3 --version`.

### API key
`check_setup.py` creates a gitignored **`.env` file** the first time you run it — never paste your key into a script. Open the `.env`, paste your key after `ANTHROPIC_API_KEY=` (no quotes, no spaces), save, and re-run. The key never touches the code, and it survives across runs so you paste it once. A single `.env` at the repo root serves every script (the loader walks up the folders to find it). You can also set `ANTHROPIC_API_KEY` in your shell — it wins over the file. A key starts with `sk-ant-`, and it must be a **workspace** key from the Console, since memory stores live in a workspace.

---

## Still stuck?
Run `python check_setup.py` and read the message — it prints a specific next step rather than a raw traceback. If it points you back here, the venv path at the top resolves it in the large majority of cases. For problems that are about the *exercise* rather than setup — stale state files, a hung session, a flat demo — see [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md).
