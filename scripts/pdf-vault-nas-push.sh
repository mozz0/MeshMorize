#!/usr/bin/env bash
# Push the PDF memory vault to the NAS. Tries LAN first, then Tailscale.
# Safe: rsync only adds/updates, never deletes. Works when NAS is reachable.
#
# SECURITY (Aug 16 2026): NO credentials in this file and no passwords needed —
# SSH key auth (~/.ssh/mesh_nas). Host verification is ON (known_hosts).
set -u

VAULT="$HOME/.openclaw/workspace/memory/pdf-vault"
NAS_USER="master"
KEY="$HOME/.ssh/mesh_nas"

if [ ! -f "$KEY" ]; then
  echo "❌ SSH key missing: $KEY"
  exit 1
fi

SSH_OPTS="-i $KEY -o BatchMode=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$HOME/.ssh/known_hosts"

for HOST in 192.168.3.2 100.109.128.123; do
  if ping -c 1 -W 2 "$HOST" >/dev/null 2>&1 || timeout 5 bash -c "</dev/tcp/$HOST/22" 2>/dev/null; then
    echo "NAS reachable at $HOST"
    # Confirmed target (attached HDD): /export/Greg/pdf-vault
    TARGET="/export/Greg/pdf-vault"
    echo "Syncing to $HOST:$TARGET"
    rsync -az --no-perms --chmod=Du=rwx,Dgo=rx,Fu=rw,Fgo=r \
      -e "ssh $SSH_OPTS" \
      "$VAULT/" "$NAS_USER@$HOST:$TARGET/" && {
      echo "✅ PDF vault synced to NAS ($TARGET)"
      exit 0
    }
    echo "⚠️ rsync to $HOST failed, trying next..."
  fi
done
echo "❌ NAS unreachable (LAN + Tailscale). Will retry on next run."
exit 1
