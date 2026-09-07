#!/usr/bin/env bash
# Expose the local Metabase dashboards to teammates via a Cloudflare quick tunnel,
# using Metabase public (read-only, no-login) dashboard links.
#
# Run it yourself:  ! bash metabase/publish.sh
# Stop sharing:     ! bash metabase/publish.sh stop
set -uo pipefail

MB="http://localhost:3000"
EMAIL="admin@dvd.local"
PASS="Dvdproj123!"
BIN="$HOME/.local/bin/cloudflared"
LOG="/tmp/dvd-cloudflared.log"
PIDFILE="/tmp/dvd-cloudflared.pid"
UUIDS="$HOME/.config/dvd-metabase-public-uuids"

if [ "${1:-}" = "stop" ]; then
  [ -f "$PIDFILE" ] && kill "$(cat "$PIDFILE")" 2>/dev/null && echo "tunnel stopped" || echo "no tunnel running"
  rm -f "$PIDFILE"
  exit 0
fi

echo "== login =="
TOK=$(curl -s -X POST -H "Content-Type: application/json" \
  -d "{\"username\":\"$EMAIL\",\"password\":\"$PASS\"}" "$MB/api/session" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
[ -n "$TOK" ] || { echo "login failed"; exit 1; }

echo "== enable public sharing =="
curl -s -X PUT -H "Content-Type: application/json" -H "X-Metabase-Session: $TOK" \
  -d '{"value":true}' "$MB/api/setting/enable-public-sharing" >/dev/null

echo "== find the consolidated dashboard =="
DID=$(curl -s -H "X-Metabase-Session: $TOK" "$MB/api/dashboard" \
  | python3 -c "import sys,json
ds=json.load(sys.stdin)
m=[d for d in ds if not d.get('archived') and 'Marketplace Weekly Dashboard' in d.get('name','')]
print(m[0]['id'] if m else '')")
[ -n "$DID" ] || { echo "consolidated dashboard not found (run provision_single.py)"; exit 1; }

echo "== create public dashboard link =="
: > "$UUIDS"
uuid=$(curl -s -X POST -H "Content-Type: application/json" -H "X-Metabase-Session: $TOK" \
  -d '{}' "$MB/api/dashboard/$DID/public_link" \
  | python3 -c "import sys,json;print(json.load(sys.stdin).get('uuid',''))")
name=$(curl -s -H "X-Metabase-Session: $TOK" "$MB/api/dashboard/$DID" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['name'])")
echo "$DID|$name|$uuid" >> "$UUIDS"
cat "$UUIDS"

echo "== install cloudflared if missing =="
if [ ! -x "$BIN" ]; then
  mkdir -p "$HOME/.local/bin"
  curl -sSL -o "$BIN" \
    https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
  chmod +x "$BIN"
fi
"$BIN" --version

echo "== start cloudflare quick tunnel =="
[ -f "$PIDFILE" ] && kill "$(cat "$PIDFILE")" 2>/dev/null || true
: > "$LOG"
nohup "$BIN" tunnel --no-autoupdate --url "$MB" >>"$LOG" 2>&1 &
echo $! > "$PIDFILE"

echo -n "   waiting for public URL"
BASE=""
for _ in $(seq 1 30); do
  BASE=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG" | head -1)
  [ -n "$BASE" ] && break
  echo -n "."; sleep 2
done
echo
[ -n "$BASE" ] || { echo "tunnel URL not found; see $LOG"; tail -5 "$LOG"; exit 1; }

echo "== point Metabase at the tunnel (so public pages load cleanly) =="
curl -s -X PUT -H "Content-Type: application/json" -H "X-Metabase-Session: $TOK" \
  -d "{\"value\":\"$BASE\"}" "$MB/api/setting/site-url" >/dev/null

echo
echo "=================================================================="
echo " Share these read-only links with teammates (no login needed):"
echo "=================================================================="
while IFS='|' read -r id name uuid; do
  echo "  $name"
  echo "     $BASE/public/dashboard/$uuid"
done < "$UUIDS"
echo
echo "Tunnel PID $(cat "$PIDFILE"); keep this machine + tunnel running."
echo "Stop sharing later with:  bash metabase/publish.sh stop"
