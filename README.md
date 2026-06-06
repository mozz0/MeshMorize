# MeshMorize 🧠

Multi-layer memory system for LLM agents. Fresh layer, mesh graph indexing, auto-logging, cross-layer search, and compliance checks.

Built for OpenClaw. Works with any agent that can run Python.

## Layers

| Layer | File | Purpose |
|-------|------|---------|
| **Fresh** | `memory/fresh/today.md` | Daily notes, 5-day rotation |
| **Mesh** | `memory/mesh.json` | Graph nodes + search index |
| **Log** | `scripts/auto_log` | Auto-log every interaction |
| **Search** | `scripts/memory_search` | Cross-layer search |
| **Check** | `scripts/memory_check` | 10-point compliance check |

## Quick start

```bash
mem-bridge init          # Rotate fresh layer
auto_log "msg" "reply"   # Log interaction
memory_search "query"    # Search all layers
memcheck                 # Full compliance check
```

## Install

Put `bridge.py` and `scripts/` in your agent workspace. The tools need to be on `PATH` for quick access.

## Source

https://clawhub.ai/mozz0/josh-learns
