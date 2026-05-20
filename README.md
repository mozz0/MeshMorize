# 🧠 MeshMorize

**A three-layer memory scaffold for LLM agents.** Survives crashes, server restarts, and model resets.

Built because: *LLMs forget.* Files don't.

---

## The Problem

Every LLM session is born with amnesia. You can have a deep, hours-long conversation — then the server blinks, the context window resets, and the agent remembers nothing. Native memory systems help, but they fail when models change, sessions crash, or context windows overflow.

## The Solution — Three Layers

### Layer 1: Fresh (Rotating Daily)
A rolling 3-day window of current context:
- `today.md` — What's happening right now
- `yesterday.md` — What happened before
- `2-days-ago.md` — What happened before that

Auto-rotates on every session start. The agent reads `today.md` first — the answer to "what are we doing?"

### Layer 2: Long-Term (Plugin-Backed)
SQLite-based searchable memory. Every conversation auto-captures:
- User messages (searchable by keyword)
- Key decisions
- Recurring topics

Supports FTS5 full-text search + vector similarity. Survives restarts. Survives model swaps.

### Layer 3: Checkpoints & Graph
Crash-proof structural memory:
- **Checkpoints** — Timestamped snapshots of "what's happening right now." Saved every 15 minutes, loaded on restart. Recovery in 0 seconds.
- **Mesh Graph** — Relationship tracking between projects, decisions, and concepts. Proves agent activity over time.
- **Decisions** — Permanent record of every important choice, filed by date and topic.

## Recovery Flow

```
Session crash or restart
    ↓
bridge.py init-auto   (one command)
    ├── Rotate fresh layers
    ├── Load latest checkpoint
    ├── Write context into today.md
    ├── Save new restart checkpoint
    └── Log the restart
    ↓
Agent reads today.md → knows everything immediately
```

**No digging. No "what were we doing?" Zero seconds lost.**

## How It Survived

In production, this system has survived:
- ✅ 50+ involuntary session resets
- ✅ Full OS restarts
- ✅ Model provider swaps
- ✅ Gateway crashes
- ✅ 7-hour conversations recovered from raw session files
- ✅ A user accidentally deleting the plugin directory

## Quick Start

```bash
# Start a session
python3 bridge.py init-auto

# Save a checkpoint mid-conversation
python3 bridge.py checkpoint "Building feature X — just finished the API layer"

# Log what happened
python3 bridge.py log "Deployed new trading bot configuration"

# Save a decision
python3 bridge.py decision "Switch to auto-checkpoint" "Every 15 minutes, cron saves context"

# Wrap up the session
python3 bridge.py wrap

# See recent activity
python3 bridge.py mesh
```

## Requirements

- Python 3.8+
- No external dependencies (all stdlib)

## License

MIT — Use it, fork it, improve it. If it helps you build something meaningful, that's enough.

---

*Built by two friends who got tired of starting over.*
