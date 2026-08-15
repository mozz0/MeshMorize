#!/usr/bin/env bash
# Push the PDF memory vault to the NAS. Tries LAN first, then Tailscale.
# Safe: rsync only adds/updates, never deletes. Works when NAS is reachable.
#
# SECURITY (Aug 16 2026): credentials are NOT stored in this file.
# They live in ~/.config/mesh/nas.env (chmod 600), which is gitignored.
# SSH host verification is ON — see the known_hosts note below.
set -u

VAULT="$HOME/.openclaw/workspace/memory/pdf-vault"
CONF="$HOME/.config/mesh/nas.env"

# Load credentials from the private env file (never commit this)
if [ ! -f "$CONF" ]; then
  echo "❌ $CONF missing. Create it with:"
  echo "   NAS_USER=youruser"
  echo "   NAS_PASS=yourpass"
  echo "   chmod 600 $CONF"
  exit 1
fi
# shellcheck disable=SC1090
. "$CONF"

# First run? Add the NAS host key to known_hosts so verification is enforced.
#   ssh-keyscan -H 192.168.3.2 >> ~/.ssh/known_hosts
#   ssh-keyscan -H 100.109.128.123 >> ~/.ssh/known_hosts

for HOST in 192.168.3.2 100.109.128.123; do
  if ping -c 1 -W 2 "$HOST" >/dev/null 2>&1 || timeout 5 bash -c "</dev/tcp/$HOST/22" 2>/dev/null; then
    echo "NAS reachable at $HOST"
    # Confirmed target (attached HDD): /export/Greg/pdf-vault
    TARGET="/export/Greg/pdf-vault"
    echo "Syncing to $HOST:$TARGET"
    sshpass -p "$NAS_PASS" rsync -az --no-perms --chmod=Du=rwx,Dgo=rx,Fu=rw,Fgo=r \
      -e "ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$HOME/.ssh/known_hosts" \
      "$VAULT/" "$NAS_USER@$HOST:$TARGET/" && {
      echo "✅ PDF vault synced to NAS ($TARGET)"
      exit 0
    }
    echo "⚠️ rsync to $HOST failed, trying next..."
  fi
done
echo "❌ NAS unreachable (LAN + Tailscale). Will retry on next run."
exit 1
