#!/usr/bin/env bash
# Stand up a local Postgres + Metabase stack for the Group 3 dashboards.
# Idempotent-ish: removes and recreates the two containers and the network.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NET=dvd-net
PG=dvd-postgres
MB=dvd-metabase
PG_PORT=5433          # 5432 is taken by another project's container
MB_PORT=3000
PG_USER=olist
PG_PASS=olist
PG_DB=olist

echo "== network =="
docker network inspect "$NET" >/dev/null 2>&1 || docker network create "$NET"

echo "== postgres =="
docker rm -f "$PG" >/dev/null 2>&1 || true
docker run -d --name "$PG" --network "$NET" \
  -e POSTGRES_USER="$PG_USER" -e POSTGRES_PASSWORD="$PG_PASS" -e POSTGRES_DB="$PG_DB" \
  -p "${PG_PORT}:5432" \
  -v "${HERE}/data:/data:ro" \
  postgres:16 >/dev/null

echo -n "   waiting for postgres"
until docker exec "$PG" pg_isready -U "$PG_USER" -d "$PG_DB" >/dev/null 2>&1; do
  echo -n "."; sleep 1
done
echo " ready"

echo "== load schema + data =="
docker cp "${HERE}/schema.sql" "$PG":/schema.sql
docker exec "$PG" psql -U "$PG_USER" -d "$PG_DB" -v ON_ERROR_STOP=1 -q -f /schema.sql
echo -n "   order_base rows: "; docker exec "$PG" psql -U "$PG_USER" -d "$PG_DB" -tAc "select count(*) from order_base"
echo -n "   item_base rows:  "; docker exec "$PG" psql -U "$PG_USER" -d "$PG_DB" -tAc "select count(*) from item_base"

echo "== metabase =="
docker rm -f "$MB" >/dev/null 2>&1 || true
docker run -d --name "$MB" --network "$NET" \
  -p "${MB_PORT}:3000" \
  metabase/metabase:latest >/dev/null

echo "Metabase starting at http://localhost:${MB_PORT} (first boot ~1-2 min)."
echo "Postgres reachable from Metabase as host='${PG}' port=5432 db='${PG_DB}' user='${PG_USER}'."
