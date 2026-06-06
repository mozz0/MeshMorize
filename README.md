# MeshMorize 🧠

Multi-layer memory system for LLM agents. Fresh layer, mesh graph with edges, auto-logging, fuzzy cross-layer search, and compliance checks.

Built for OpenClaw. Works with any agent that can run Python.

## Architecture

### Three-Layer Design

| Layer | What | Purpose |
|-------|------|---------|
| **Fresh** | `memory/fresh/today.md` | Daily working notes, auto-rotated 5-day cycle |
| **Mesh** | `memory/mesh.json` | Persistent graph nodes + edges for relationship search |
| **Log** | Daily `.md` files | Complete interaction history, preserved forever |

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

## Quick start

```bash
mem-bridge init          # Rotate fresh layer, create today.md
auto_log "msg" "reply"   # Log every interaction (timestamped)
memory_search "query"    # Search all layers + fuzzy matching
memcheck                 # Full 10-point compliance check
```

### Workflow

1. On session start: `mem-bridge init` (rotates fresh layer, restores checkpoint)
2. Before every response: `auto_log "user said" "agent replied"` 
3. When user references past: `memory_search "topic"` (checks fresh → daily → mesh → raw → long-term)
4. When learning something: Add to mesh via `bridge.py add-node <id> <note>`
5. Periodic: `memcheck` (verify all layers healthy)

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

All tools respect `$OPENCLAW_WORKSPACE` env var with fallback to `~/.openclaw/workspace`.

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
```

## What's New in v3.2.0

- `$OPENCLAW_WORKSPACE` env var — portable across setups
- Mesh edges — nodes now link via `triggers`, `depends_on`, `related_to`
- Fuzzy search — handles typos automatically
- `mem-bridge summarize` — auto-generates today's recap from yesterday's logs
- All tools pass `memcheck` 10-point compliance
