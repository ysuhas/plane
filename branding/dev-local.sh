#!/usr/bin/env bash
# Local dev stack on ports that don't clash with other projects.
#
#   branding/dev-local.sh up       sync the ports into the .env files, start the containers, then web/admin/space/live
#   branding/dev-local.sh down     stop the frontends and the containers (data volumes are kept)
#   branding/dev-local.sh status   what is answering where
#
# Defaults, each overridable with LOCAL_*_PORT in the root .env or the environment:
#   web 3200, admin 3201, space 3202, live 3300, api 8002, redis 6380
# The apps' own `dev` scripts hard-code 3000/3001/3002 (upstream-owned), so this runs react-router
# directly with --port instead of editing them.
set -euo pipefail
set -m # job control: each background service gets its own process group, so `down` can stop the whole tree
cd "$(dirname "$0")/.."

# LOCAL_* from the root .env (compose reads the same file for the container ports)
for kv in $(grep -E '^LOCAL_[A-Z_]+=' .env 2>/dev/null || true); do export "${kv%%=*}=$(echo "${kv#*=}" | tr -d '"')"; done
WEB=${LOCAL_WEB_PORT:-3200} ADMIN=${LOCAL_ADMIN_PORT:-3201} SPACE=${LOCAL_SPACE_PORT:-3202} LIVE=${LOCAL_LIVE_PORT:-3300}
API=${LOCAL_API_PORT:-8002} REDIS=${LOCAL_REDIS_PORT:-6380}

# Logs and PIDs go in a private per-user directory, never a shared /tmp path: a planted symlink or PID
# file there could overwrite a file or make `down` signal an unrelated process.
RUN=${XDG_STATE_HOME:-$HOME/.local/state}/scholrithm-plane-dev
COMPOSE=(docker compose -f docker-compose-local.yml -f docker-compose-local.ports.yml)
url() { echo "http://localhost:$1"; }

private_dir() {
  mkdir -p "$RUN"
  # verify before chmod, so a planted symlink can never have its target's permissions changed
  [ ! -L "$RUN" ] && [ -d "$RUN" ] && [ -O "$RUN" ] || { echo "refusing to use $RUN: not a real directory owned by you"; exit 1; }
  chmod 700 "$RUN"
}

# set KEY="value" in a git-ignored .env file, appending if the key is missing
setenv() {
  [ -f "$1" ] || return 0
  if grep -q "^$2=" "$1"; then sed -i.bak -E "s#^$2=.*#$2=\"$3\"#" "$1" && rm -f "$1.bak"; else echo "$2=\"$3\"" >> "$1"; fi
}

sync_env() {
  for app in web admin space; do
    f=apps/$app/.env
    setenv $f VITE_API_BASE_URL "$(url $API)"
    setenv $f VITE_WEB_BASE_URL "$(url $WEB)"
    setenv $f VITE_ADMIN_BASE_URL "$(url $ADMIN)"
    setenv $f VITE_SPACE_BASE_URL "$(url $SPACE)"
    setenv $f VITE_LIVE_BASE_URL "$(url $LIVE)"
  done
  f=apps/live/.env
  setenv $f PORT "$LIVE"
  setenv $f API_BASE_URL "$(url $API)"
  setenv $f WEB_BASE_URL "$(url $WEB)"
  setenv $f LIVE_BASE_URL "$(url $LIVE)"
  setenv $f REDIS_PORT "$REDIS"
  setenv $f REDIS_URL "redis://localhost:$REDIS/"
  f=apps/api/.env
  setenv $f CORS_ALLOWED_ORIGINS "$(url $WEB),$(url $ADMIN),$(url $SPACE),$(url $LIVE)"
  setenv $f APP_BASE_URL "$(url $WEB)"
  setenv $f ADMIN_BASE_URL "$(url $ADMIN)"
  setenv $f SPACE_BASE_URL "$(url $SPACE)"
  setenv $f LIVE_BASE_URL "$(url $LIVE)"
}

listener() { lsof -ti "tcp:$1" -sTCP:LISTEN 2>/dev/null || true; }

start() { # name port command...
  local name=$1 port=$2; shift 2
  if [ -n "$(listener "$port")" ]; then echo "$name: port $port already in use, leaving it alone"; return; fi
  nohup "$@" > "$RUN/$name.log" 2>&1 &
  echo $! > "$RUN/$name.pid"
}

stop() { # name: signal only a process group this script started
  local pidfile="$RUN/$1.pid" pid
  [ -f "$pidfile" ] && [ ! -L "$pidfile" ] || return 0
  pid=$(cat "$pidfile"); rm -f "$pidfile"
  # numeric, and the group leader is still our pnpm wrapper; anything else is stale or not ours
  if [[ "$pid" =~ ^[0-9]+$ ]] && ps -o command= -p "$pid" 2>/dev/null | grep -q pnpm; then
    kill -- "-$pid" 2>/dev/null || true
  else
    echo "$1: stale or foreign pid file ignored"
  fi
}

wait_for() { # label url
  for _ in $(seq 1 90); do
    [ "$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "$2" || true)" = 200 ] && { echo "up: $1 $2"; return; }
    sleep 2
  done
  echo "NOT READY after 180s: $1 $2 (see $RUN/*.log or: docker compose logs)"; return 1
}

case "${1:-}" in
  up)
    private_dir
    sync_env
    "${COMPOSE[@]}" up -d --build
    wait_for api "$(url $API)/api/instances/"
    start web "$WEB" pnpm --filter web exec react-router dev --port "$WEB"
    start admin "$ADMIN" pnpm --filter admin exec react-router dev --port "$ADMIN"
    start space "$SPACE" pnpm --filter space exec react-router dev --port "$SPACE"
    start live "$LIVE" pnpm --filter live dev
    wait_for web "$(url $WEB)/"
    wait_for admin "$(url $ADMIN)/god-mode/"
    wait_for space "$(url $SPACE)/spaces/"
    echo; echo "web   $(url $WEB)"; echo "admin $(url $ADMIN)/god-mode"; echo "space $(url $SPACE)/spaces"; echo "logs  $RUN/*.log"
    ;;
  down)
    private_dir
    stop web; stop admin; stop space; stop live
    sleep 1
    for p in "$WEB" "$ADMIN" "$SPACE" "$LIVE"; do
      [ -z "$(listener "$p")" ] || echo "port $p is still in use by something this script did not start"
    done
    "${COMPOSE[@]}" down
    ;;
  status)
    for t in "web $(url $WEB)/" "admin $(url $ADMIN)/god-mode/" "space $(url $SPACE)/spaces/" "api $(url $API)/api/instances/"; do
      set -- $t; printf "%-6s %s -> %s\n" "$1" "$2" "$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "$2" || true)"
    done
    "${COMPOSE[@]}" ps --format 'table {{.Service}}\t{{.State}}\t{{.Ports}}'
    ;;
  *) echo "usage: $0 up|down|status"; exit 1 ;;
esac
