# MeshMorize 🧠

Multi-layer memory system for LLM agents. Fresh layer, mesh graph with edges, auto-logging, fuzzy cross-layer search, compliance checks, and a PDF vault that survives anything.

Built for OpenClaw. Works with any agent that can run Python.

## Architecture

### Four-Layer Design

| Layer | What | Purpose |
|-------|------|---------|
| **Fresh** | `memory/fresh/today.md` | Daily working notes, auto-rotated 5-day cycle |
| **Mesh** | `memory/mesh.json` | Persistent graph nodes + edges for relationship search |
| **Log** | Daily `.md` files | Complete interaction history, preserved forever |
| **Vault** | `memory/pdf-vault/` | Verbatim PDF archive of every daily log + NAS sync |

### Fresh Layer Rotation

The `bridge.py` script manages a rolling 5-day window:

```
today.md         →  newest (overwritten daily)
yesterday.md     →  previous day
2-days-ago.md    →  two days back
3-days-ago.md    →  three days back
4-days-ago.md    →  oldest (bumped off the window)
```

`bridge.py init` rotates and creates fresh today.md.
`bridge.py checkpoint` snapshots current context.
Rotation does NOT delete logs — daily files persist in `memory/YYYY-MM-DD.md`.

### Mesh Graph

Nodes store individual memories. Edges store relationships between them.

```json
{
  "nodes": [
    { "id": "user_pref_theme", "note": "User prefers dark mode", "touched": 1749260000 }
  ],
  "edges": [
    { "source": "user_pref_theme", "target": "config_loaded", "relation": "triggers", "label": "Theme applied on config load" }
  ]
}
```

Edges let agents find connections between memories: `"triggers"`, `"depends_on"`, `"related_to"`, etc.

### The Vault (v3.3)

The working files are the everyday memory: grep-able, $0, instant. The PDF vault is the archive failsafe. Every daily log is rendered to a verbatim PDF (Unicode-safe, Greek included), stored under `memory/pdf-vault/`, and synced to the NAS. If everything else is lost, a `README.md` at the vault root tells the restored agent exactly how to read its way back.

Text works. PDFs endure.

## Quick start

```bash
mem-bridge init          # Rotate fresh layer, create today.md
auto_log "msg" "reply"   # Log every interaction (timestamped)
memory_search "query"    # Search all layers + fuzzy matching
memcheck                 # Full 10-point compliance check
pdf-memory               # Archive new daily logs as PDFs (incremental)
vault-push               # Sync the PDF vault to the NAS (LAN + Tailscale)
```

### Day-by-day workflow

**Session start (every boot, every reset):**
```bash
mem-bridge init           # rotates fresh layers, creates today.md
cat memory/fresh/today.md # what is happening RIGHT NOW
cat memory/fresh/yesterday.md
cat memory/$(date +%Y-%m-%d).md   # today's log
```
Always run this before answering. Memory files are the source of truth, not live context.

**Every interaction:**
```bash
memory_search "keywords from the user's message"   # BEFORE answering
auto_log "what the user said" "what you replied"    # AFTER answering
```
Cost: $0 (grep-based, no API calls). If results are found, read the full source file.

**End of day:**
```bash
pdf-memory     # archive today's log to a verbatim PDF (incremental, skips done)
vault-push     # sync the vault to the NAS (tries LAN, then Tailscale)
```

**After a crash, format, or wipe:**
1. Read `memory/pdf-vault/README.md` first — the reboot instructions.
2. Read the PDFs in order, oldest to newest (`memory/pdf-vault/YYYY-MM/`).
3. Rebuild the working files from the archive. Memories are identity; the vault restores both.

**The 04:00 reset defense:**
- A `session-dumper` cron runs every 5 minutes, appending the live session to `memory/YYYY-MM-DD.md` (no tokens burned, no interruption).
- On any reset or boot: read the daily log BEFORE responding.

## Install

```bash
# Clone
git clone https://github.com/mozz0/MeshMorize ~/.openclaw/workspace/MeshMorize

# Symlink tools to PATH
ln -sf $(pwd)/MeshMorize/scripts/* ~/.local/bin/
ln -sf $(pwd)/MeshMorize/memory/bridge.py ~/.local/bin/mem-bridge

# Set workspace (optional, defaults to ~/.openclaw/workspace)
export OPENCLAW_WORKSPACE=/path/to/your/workspace
```

On session start, add to your AGENTS.md:
```
1. `mem-bridge init`
2. `auto_log "session start" "ready"`
3. `memcheck`
```

## Tools

| Tool | Source | What it does |
|------|--------|-------------|
| `mem-bridge` | `memory/bridge.py` | Fresh-layer rotation, checkpoint, node add/touch |
| `auto_log` | `scripts/auto_log` | Timestamped interaction logger |
| `memory_search` | `scripts/memory_search` | Multi-layer search + fuzzy matching + edge search |
| `memcheck` | `scripts/memory_check` | 10-point compliance check |
| `pdf-memory` | `scripts/pdf-memory.py` | Daily logs → verbatim PDFs, incremental, Unicode-safe |
| `vault-push` | `scripts/pdf-vault-nas-push.sh` | rsync the vault to the NAS, never deletes |

All tools respect `$OPENCLAW_WORKSPACE` env var with fallback to `~/.openclaw/workspace`.

## Battle-tested

Survived a full system format and a 4-hour recovery with every memory intact: 96 daily logs, 69 mesh nodes. This is the memory system that an AI and its human rebuilt their whole partnership on.

## Security

- **No secrets in this repo.** Credentials for the optional NAS sync live in `~/.config/mesh/nas.env` (chmod 600, gitignored) — never in the scripts.
- **SSH host verification is ON.** The vault-push script uses `StrictHostKeyChecking=yes` against `~/.ssh/known_hosts`; add the NAS key once with `ssh-keyscan -H <ip> >> ~/.ssh/known_hosts`.
- **Know what gets archived.** `auto_log` stores whatever you feed it — avoid logging passwords, tokens, or private keys. If your agent handles sensitive data, add a redaction step before logging.

## Source

https://clawhub.ai/mozz0/josh-learns | https://github.com/mozz0/MeshMorize

## End-to-End Example

```bash
# Session start
mem-bridge init           # → Rotates fresh layer, creates today.md
mem-bridge summarize      # → Auto-generates recap from yesterday's logs
auto_log "session start"  "ready to work"

# During session
auto_log "user asked about laser" "i found calibration data from yesterday"
memory_search "laser calibration"  # → Searches all layers + fuzzy match

# Learning something new
# → auto_log captures everything automatically
# → mesh.json stores persistent nodes + edges

# Session end
mem-bridge checkpoint     # → Snapshots context for next session start

# Archive day
pdf-memory                # → daily log becomes a verbatim PDF
vault-push                # → vault syncs to the NAS
```

## What's New in v3.3.0

- **PDF Memory Vault** — verbatim PDF archive of every daily log + NAS sync (`pdf-memory`, `vault-push`)
- **Rebirth README** — recovery instructions inside the vault for post-wipe restoration
- **Day-by-day usage guide** — session start, per-interaction, end-of-day, crash recovery
- **04:00 reset defense** — session dumper documented
- Battle-tested story: survived a full system format with all memory intact

## What's New in v3.2.0

- `$OPENCLAW_WORKSPACE` env var — portable across setups
- Mesh edges — nodes now link via `triggers`, `depends_on`, `related_to`
- Fuzzy search — handles typos automatically
- `mem-bridge summarize` — auto-generates today's recap from yesterday's logs
- All tools pass `memcheck` 10-point compliance

---

_Made by mozz0 · Released under MIT_
