#!/usr/bin/env bash
# Serve the production build and expose it via a Cloudflare quick tunnel.
#   bash webapp/publish.sh          # start app + tunnel, print public URL
#   bash webapp/publish.sh stop     # stop tunnel + app
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT=3001
BIN="$HOME/.local/bin/cloudflared"
TLOG=/tmp/dvd-webapp-cf.log
APIDF=/tmp/dvd-webapp-app.pid
TPIDF=/tmp/dvd-webapp-cf.pid

if [ "${1:-}" = "stop" ]; then
  for f in "$TPIDF" "$APIDF"; do [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null; rm -f "$f"; done
  pkill -f "next-server" 2>/dev/null
  echo "stopped"; exit 0
fi

cd "$HERE"
if ! ss -ltn 2>/dev/null | grep -q ":$PORT"; then
  echo "== starting Next production server on :$PORT =="
  PORT=$PORT nohup npm run start >/tmp/dvd-webapp-app.log 2>&1 &
  echo $! > "$APIDF"
  for _ in $(seq 1 30); do curl -sf "http://localhost:$PORT/api/meta" -o /dev/null && break; sleep 1; done
fi

echo "== starting cloudflare quick tunnel =="
[ -f "$TPIDF" ] && kill "$(cat "$TPIDF")" 2>/dev/null || true
: > "$TLOG"
nohup "$BIN" tunnel --no-autoupdate --url "http://localhost:$PORT" >>"$TLOG" 2>&1 &
echo $! > "$TPIDF"

echo -n "   waiting for URL"
URL=""
for _ in $(seq 1 30); do
  URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$TLOG" | head -1)
  [ -n "$URL" ] && break; echo -n "."; sleep 2
done
echo
[ -n "$URL" ] && echo "PUBLIC URL: $URL" || { echo "no URL; see $TLOG"; tail -5 "$TLOG"; }
