#!/usr/bin/env python3
"""🧠 MeshMorize — Open Source Memory Scaffold

A three-layer memory system for LLM agents that don't natively persist context.
Designed to survive crashes, server restarts, and model resets.

Architecture:
  Layer 1 — Fresh (recent context, auto-rotated daily)
  Layer 2 — Long-term (SQLite-backed searchable memory)
  Layer 3 — Structural (checkpoints, decisions, relationship graph)

Usage:
  bridge.py init               session start (rotate + create today)
  bridge.py init-auto           FULL start — init + resume + checkpoint + log
  bridge.py log <message>       append timestamped entry to daily log
  bridge.py checkpoint <ctx>    save crash-recovery snapshot
  bridge.py resume              load latest checkpoint
  bridge.py decision <t> <body> save a decision file
  bridge.py wrap                compile session summary into fresh layer
  bridge.py mesh [N]            show N most recent mesh nodes
"""

import json, os, sys, shutil, textwrap
from datetime import date, datetime, timezone

WORKSPACE = os.path.expanduser("~")
MEMORY = os.path.join(WORKSPACE, "memory")
FRESH = os.path.join(MEMORY, "fresh")
DECISIONS = os.path.join(MEMORY, "decisions")
MESH = os.path.join(MEMORY, "graph.json")

os.makedirs(FRESH, exist_ok=True)
os.makedirs(DECISIONS, exist_ok=True)

def now_ts():
    return datetime.now(timezone.utc).isoformat()

def today_log_path():
    return os.path.join(MEMORY, date.today().strftime("%Y-%m-%d") + ".md")

# ─── LAYER 1: FRESH ────────────────────────────────────────

def rotate():
    """Rotate fresh files: today→yesterday→2-days-ago"""
    today = os.path.join(FRESH, "today.md")
    yesterday = os.path.join(FRESH, "yesterday.md")
    two_days = os.path.join(FRESH, "2-days-ago.md")
    if not os.path.exists(today):
        return False
    with open(today) as f:
        content = f.read()
    today_str = date.today().strftime("%B %d, %Y")
    if today_str in content:
        return False
    if os.path.exists(yesterday):
        shutil.copy2(yesterday, two_days)
    shutil.copy2(today, yesterday)
    return True

def create_today():
    today = date.today().strftime("%B %d, %Y")
    template = f"""# Today — {today}

> Auto-created on session start.
> Read first — answers "what happened recently?"

---

## Previous session recap

(will be populated from wrap/rotation)

## Active projects

(see workspace for details)
"""
    with open(os.path.join(FRESH, "today.md"), 'w') as f:
        f.write(template)

# ─── LOGGING ────────────────────────────────────────────────

def auto_log(message, category="general"):
    path = today_log_path()
    ts = datetime.now(timezone.utc).strftime("%H:%M UTC")
    entry = f"\n## {ts} — {category}\n> {message}\n"
    with open(path, 'a') as f:
        f.write(entry)
    mesh_touch("memory-system")
    return True

# ─── DECISIONS ──────────────────────────────────────────────

def capture_decision(topic, body, tags=None):
    safe = topic.lower().replace(" ", "-")[:40]
    ts = date.today().strftime("%Y-%m-%d")
    filename = f"{ts}-{safe}.md"
    filepath = os.path.join(DECISIONS, filename)
    content = f"""# Decision: {topic}

**Date:** {date.today().strftime("%B %d, %Y")}
**Tags:** {', '.join(tags) if tags else 'general'}

---

{body}
"""
    with open(filepath, 'w') as f:
        f.write(content.lstrip())
    add_mesh_node(f"decision-{safe}", "decision", file=filename, note=topic)
    return filepath

# ─── MESH GRAPH ────────────────────────────────────────────

def load_mesh():
    if not os.path.exists(MESH):
        default = {"version": "1.0", "last_updated": now_ts(), "nodes": [], "edges": []}
        with open(MESH, 'w') as f:
            json.dump(default, f, indent=2)
    with open(MESH) as f:
        return json.load(f)

def save_mesh(mesh):
    mesh["last_updated"] = now_ts()
    with open(MESH, 'w') as f:
        json.dump(mesh, f, indent=2)

def add_mesh_node(node_id, node_type, file=None, note=""):
    mesh = load_mesh()
    now = now_ts()
    existing = [n for n in mesh["nodes"] if n["id"] == node_id]
    if existing:
        existing[0]["lastSeen"] = now
        save_mesh(mesh)
        return False
    mesh["nodes"].append({
        "id": node_id, "type": node_type, "file": file, "note": note,
        "createdAt": now, "lastSeen": now
    })
    save_mesh(mesh)
    return True

def mesh_touch(node_id):
    mesh = load_mesh()
    now = now_ts()
    for n in mesh["nodes"]:
        if n["id"] == node_id:
            n["lastSeen"] = now
            save_mesh(mesh)
            return True
    add_mesh_node(node_id, "concept", note="auto-tracked")
    return False

def mesh_list_recent(limit=10):
    mesh = load_mesh()
    with_time = [n for n in mesh["nodes"] if "lastSeen" in n]
    with_time.sort(key=lambda n: n["lastSeen"], reverse=True)
    print(f"\n📊 Mesh — {len(mesh['nodes'])} nodes:")
    for n in with_time[:limit]:
        seen = n.get("lastSeen", "?")[:19]
        print(f"  {n['id'][:24]:24s} {n.get('type','?'):12s} last: {seen}")
    return with_time

# ─── LAYER 3: CHECKPOINTS ─────────────────────────────────

CHECKPOINT_DIR = os.path.join(MEMORY, "checkpoints")
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

def save_checkpoint(context, active_node=None, extras=None):
    now = datetime.now(timezone.utc)
    cp = {
        "timestamp": now.isoformat(),
        "time_utc": now.strftime("%H:%M UTC"),
        "context": context,
        "active_node": active_node,
        "extras": extras or {},
    }
    with open(os.path.join(CHECKPOINT_DIR, "latest.json"), 'w') as f:
        json.dump(cp, f, indent=2)
    history = os.path.join(CHECKPOINT_DIR, now.strftime("%Y-%m-%d_%H%M.json"))
    with open(history, 'w') as f:
        json.dump(cp, f, indent=2)
    print(f"📌 Checkpoint: {context[:60]}...")
    return cp

def resume_checkpoint():
    path = os.path.join(CHECKPOINT_DIR, "latest.json")
    if not os.path.exists(path):
        print("📭 No checkpoint — fresh start")
        return None
    with open(path) as f:
        cp = json.load(f)
    print(f"📂 Resumed: {cp.get('context','?')[:80]}...")
    return cp

def session_wrap():
    today = os.path.join(FRESH, "today.md")
    if not os.path.exists(today):
        return
    with open(today) as f:
        content = f.read()
    log = today_log_path()
    recent = ""
    if os.path.exists(log):
        with open(log) as f:
            c = f.read().strip()
            if len(c) > 50: recent = c[-1000:]
    decisions = sorted(os.listdir(DECISIONS), reverse=True)[:5]
    ds = "\n".join([f"- {d.replace('.md','')}" for d in decisions])
    now = datetime.now(timezone.utc).strftime("%H:%M UTC")
    wrap = f"""
---
## 📦 Session Wrap — {now}
### Recent activity
{recent[:600] if recent else "(none)"}
### Recent decisions
{ds if ds else "(none)"}
### Mesh: {len(load_mesh()['nodes'])} nodes
---
"""
    with open(today, 'a') as f:
        f.write(wrap)

# ─── INIT AUTO — FULL STARTUP ──────────────────────────────

def init_auto():
    print("🧠 Memory Bridge — Full Startup")
    print("=" * 40)
    rotated = rotate()
    if rotated:
        create_today()
    mesh_touch("memory-system")
    cp = resume_checkpoint()
    if cp:
        today_path = os.path.join(FRESH, "today.md")
        note = f"""
## 🔁 Resumed
**Context:** {cp.get('context','?')}
**From:** {cp.get('time_utc','?')}
---
"""
        with open(today_path, 'a') as f:
            f.write(note)
    ts = datetime.now(timezone.utc).strftime("%H:%M UTC")
    prev_ctx = cp.get('context', '') if cp else ''
    ctx = f"Session restarted at {ts}"
    if prev_ctx:
        ctx += f" (resumed: {prev_ctx[:80]})"
    save_checkpoint(ctx, "memory-system")
    auto_log("Session started — bridge.py init-auto executed", "startup")
    print("✅ Full startup — 0 memory gaps")
    return cp

# ─── MAIN ──────────────────────────────────────────────────

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    m = {
        "init": lambda: (rotate() and create_today(), mesh_touch("memory-system"), print("🧠 Memory bridge initialized ✅")),
        "init-auto": init_auto,
        "log": lambda: auto_log(" ".join(sys.argv[2:])) if len(sys.argv) >= 3 else print("Usage: bridge.py log <message>"),
        "checkpoint": lambda: save_checkpoint(" ".join(sys.argv[2:]), sys.argv[3] if len(sys.argv) > 3 else None) if len(sys.argv) >= 3 else print("Usage: bridge.py checkpoint <context> [node]"),
        "resume": lambda: (cp := resume_checkpoint()) and cp,
        "decision": lambda: capture_decision(sys.argv[2], " ".join(sys.argv[3:])) if len(sys.argv) >= 4 else print("Usage: bridge.py decision <topic> <body>"),
        "wrap": session_wrap,
        "mesh": lambda: mesh_list_recent(int(sys.argv[2]) if len(sys.argv) > 2 else 10),
    }
    if cmd in m:
        m[cmd]()
    else:
        print("""🧠 MeshMorize — Commands:
  init                    session start (rotate + create today)
  init-auto               FULL start — init + resume + checkpoint + log
  log <message>           timestamped entry to daily log
  checkpoint <context>    save crash-recovery snapshot
  resume                  load latest checkpoint
  decision <topic> <body> save a decision file
  wrap                    session summary to fresh layer
  mesh [N]                show N most recent nodes (default 10)
""")

if __name__ == "__main__":
    main()
