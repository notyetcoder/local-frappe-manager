#!/usr/bin/env bash
#
# local-bench installer
#
# What this does, in order:
#   1. Sanity-checks the environment (Linux/WSL, not running as root)
#   2. Installs Docker if it isn't already installed
#   3. Builds a custom Frappe image that includes ERPNext + our
#      local_bench app, using frappe_docker's documented custom-apps
#      build method (apps.json + APPS_JSON_BASE64 build arg)
#   4. Brings up the container stack (mariadb, redis, backend, frontend,
#      websocket, queue workers, scheduler)
#   5. Creates the first site, installs local_bench on it
#   6. Prints the URL to open in your browser
#
# Usage (inside WSL Ubuntu or native Ubuntu 22.04):
#   chmod +x install.sh
#   ./install.sh
#
# Re-running this script is safe — it checks what's already done and
# skips steps that don't need repeating.

set -euo pipefail

# WSL shares the Windows PATH into Linux by default. If Docker Desktop is
# installed on Windows, its docker.exe can end up resolving ahead of the
# native Linux docker this script installs below - and Windows' docker.exe
# doesn't know about Linux-side CLI plugins like compose, which produces a
# confusing "compose not found" error even though it's correctly installed.
# Forcing Linux system paths first, for this script's own execution, avoids
# that whole class of conflict.
export PATH="/usr/bin:/usr/local/bin:/usr/sbin:$PATH"

# ---- config -----------------------------------------------------------

PROJECT_NAME="local-bench"
SITE_NAME="local-bench.localhost"
FRAPPE_BRANCH="version-15"

# TODO: once local_bench is published as its own GitHub repo, put the
# real URL here. Until then this points at a placeholder — replace
# before distributing this script publicly.
LOCAL_BENCH_APP_REPO="https://github.com/notyetcoder/local-frappe-manager"
LOCAL_BENCH_APP_BRANCH="main"

# bench clones apps by the repo's URL slug, so this must match the repo
# name above exactly - it's the folder name the app ends up in under
# apps/ inside the container.
LOCAL_BENCH_APP_FOLDER="local-frappe-manager"

INSTALL_DIR="$HOME/.local-bench"
FRAPPE_DOCKER_DIR="$INSTALL_DIR/frappe_docker"

# ---- helpers ------------------------------------------------------------

log()  { printf '\n\033[1;36m==>\033[0m %s\n' "$1"; }
warn() { printf '\033[1;33m[warning]\033[0m %s\n' "$1"; }
fail() { printf '\033[1;31m[error]\033[0m %s\n' "$1"; exit 1; }

# ---- 1. environment checks ---------------------------------------------

log "Checking environment"

if [[ "$(uname -s)" != "Linux" ]]; then
  fail "This script must run inside a Linux environment. On Windows, install WSL first: open PowerShell as Administrator and run 'wsl --install -d Ubuntu-22.04', then re-run this script inside that Ubuntu terminal."
fi

if [[ "$EUID" -eq 0 ]]; then
  fail "Don't run this as root/sudo directly. Run it as your normal user — it will ask for your password only when it needs to install Docker."
fi

if grep -qi microsoft /proc/version 2>/dev/null; then
  log "WSL detected — good."
  if ! grep -q "systemd=true" /etc/wsl.conf 2>/dev/null; then
    warn "systemd doesn't look enabled in WSL. If Docker fails to start below, run:"
    warn "  sudo bash -c 'printf \"[boot]\\nsystemd=true\\n\" >> /etc/wsl.conf'"
    warn "then run 'wsl --shutdown' in PowerShell, reopen Ubuntu, and re-run this script."
  fi
fi

# ---- 2. install docker ---------------------------------------------------

if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
  log "Docker already installed and running — skipping."
else
  log "Installing Docker (this needs your password)"
  curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
  sudo sh /tmp/get-docker.sh
  sudo usermod -aG docker "$USER"
  rm -f /tmp/get-docker.sh

  warn "Docker was just installed. Group membership needs a fresh shell to take effect."
  warn "Re-run this script now — it will pick up right where it left off."
  # Re-exec under the new group without requiring the user to close their
  # terminal manually.
  exec sg docker -c "$0 $*"
fi

if ! docker compose version &>/dev/null; then
  warn "docker compose isn't working. Here's what's actually happening:"
  echo "--- which docker (all matches on PATH) ---"
  which -a docker 2>&1 || true
  echo "--- docker compose version (real error) ---"
  docker compose version 2>&1 || true
  echo "--- cli-plugins directories ---"
  ls -la /usr/libexec/docker/cli-plugins/ 2>&1 || true
  ls -la /usr/lib/docker/cli-plugins/ 2>&1 || true
  ls -la "$HOME/.docker/cli-plugins/" 2>&1 || true
  echo "-------------------------------------------"
  fail "See the diagnostic output above. If 'which -a docker' shows more than one path, you likely have both Docker Desktop's WSL integration AND a separate native Docker engine installed side by side, and they disagree about where the compose plugin lives — that's a real conflict to resolve manually (e.g. disable Docker Desktop's WSL integration for this distro if you want to use the native engine this script installed, or vice versa), not something safe for this script to silently paper over."
fi

# ---- 3. build custom image with erpnext + local_bench -------------------

log "Setting up frappe_docker"
mkdir -p "$INSTALL_DIR"
if [[ ! -d "$FRAPPE_DOCKER_DIR" ]]; then
  git clone https://github.com/frappe/frappe_docker "$FRAPPE_DOCKER_DIR"
else
  log "frappe_docker already cloned — pulling latest"
  git -C "$FRAPPE_DOCKER_DIR" pull --ff-only || warn "Couldn't fast-forward frappe_docker, continuing with existing copy."
fi

log "Writing apps.json (local_bench only — other apps like ERPNext are installed later, from the dashboard itself)"
cat > "$INSTALL_DIR/apps.json" <<EOF
[
  {
    "url": "${LOCAL_BENCH_APP_REPO}",
    "branch": "${LOCAL_BENCH_APP_BRANCH}"
  }
]
EOF

APPS_JSON_BASE64=$(base64 -w 0 "$INSTALL_DIR/apps.json")
# Tag by a hash of the actual build inputs, not a fixed name — this way a
# change to apps.json (e.g. adding/removing an app) always produces a new
# tag and triggers a real rebuild, instead of silently reusing a stale
# image that was built from different inputs.
BUILD_HASH=$(printf '%s%s' "${APPS_JSON_BASE64}" "${FRAPPE_BRANCH}" | sha256sum | cut -c1-12)
IMAGE_TAG="local-bench-custom:${BUILD_HASH}"

if docker image inspect "${IMAGE_TAG}" &>/dev/null; then
  log "Image ${IMAGE_TAG} already built — skipping (delete it with 'docker rmi ${IMAGE_TAG}' to force a rebuild)"
else
  log "Building custom image (this can take 10-20 minutes the first time)"
  docker build \
    --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
    --build-arg=FRAPPE_BRANCH="${FRAPPE_BRANCH}" \
    --build-arg=APPS_JSON_BASE64="${APPS_JSON_BASE64}" \
    --tag="${IMAGE_TAG}" \
    --file="${FRAPPE_DOCKER_DIR}/images/layered/Containerfile" \
    "${FRAPPE_DOCKER_DIR}"
fi

# ---- 4. bring up the stack ------------------------------------------------

log "Writing docker compose environment"
ENV_FILE="$INSTALL_DIR/.env"
# Defaults so nothing ever prompts for input. Override either by exporting
# these before running the script, e.g.:
#   LOCAL_BENCH_DB_PASSWORD=something LOCAL_BENCH_ADMIN_PASSWORD=something ./install.sh
# Fine as-is for local-only use (nothing here is exposed to the internet);
# change it if this bench will ever be reachable from outside your machine.
DB_PASSWORD="${LOCAL_BENCH_DB_PASSWORD:-frappeP}"
ADMIN_PASSWORD="${LOCAL_BENCH_ADMIN_PASSWORD:-frappeP}"

cat > "$ENV_FILE" <<EOF
CUSTOM_IMAGE=${IMAGE_TAG%:*}
CUSTOM_TAG=${IMAGE_TAG#*:}
DB_PASSWORD=${DB_PASSWORD}
SITE_NAME=${SITE_NAME}
EOF

echo "$INSTALL_DIR/.env written. MariaDB root password and admin password saved to:"
echo "  $INSTALL_DIR/passwords.txt"
cat > "$INSTALL_DIR/passwords.txt" <<EOF
DB root password: ${DB_PASSWORD}
Administrator password: ${ADMIN_PASSWORD}
Site: http://${SITE_NAME}
EOF
chmod 600 "$INSTALL_DIR/passwords.txt"

log "Starting containers"
docker compose \
  --project-name "$PROJECT_NAME" \
  --env-file "$ENV_FILE" \
  -f "$FRAPPE_DOCKER_DIR/compose.yaml" \
  -f "$FRAPPE_DOCKER_DIR/overrides/compose.mariadb.yaml" \
  -f "$FRAPPE_DOCKER_DIR/overrides/compose.redis.yaml" \
  up -d --pull never

log "Waiting for the database to be ready"
sleep 15

log "Saving DB root password to bench config (so the dashboard can create sites later without prompting for it)"
docker compose --project-name "$PROJECT_NAME" exec backend \
  bench set-config -g root_password "${DB_PASSWORD}"

# ---- 5. create site + install our app ------------------------------------

log "Creating site ${SITE_NAME} and installing local_bench (your other apps — ERPNext, CRM, etc. — get installed next, from the dashboard itself)"
if docker compose --project-name "$PROJECT_NAME" exec backend test -d "sites/${SITE_NAME}" 2>/dev/null; then
  log "Site ${SITE_NAME} already exists — skipping (drop it first with 'bench drop-site ${SITE_NAME}' inside the backend container to recreate)"
else
  docker compose --project-name "$PROJECT_NAME" exec backend \
    bench new-site "${SITE_NAME}" \
      --mariadb-root-password "${DB_PASSWORD}" \
      --admin-password "${ADMIN_PASSWORD}" \
      --install-app local_bench \
      --set-default
fi

log "Building the local-bench dashboard frontend (first time only, ~1-2 min)"
docker compose --project-name "$PROJECT_NAME" exec backend \
  bash -c "cd apps/${LOCAL_BENCH_APP_FOLDER}/frontend && npm install --no-audit --no-fund && npm run build"

# ---- 6. done --------------------------------------------------------------

log "Done"
echo ""
echo "  Open this in your browser:  http://${SITE_NAME}/local-bench"
echo "  Username: Administrator"
echo "  Password: (see $INSTALL_DIR/passwords.txt)"
echo ""
echo "This site has the dashboard installed, but no apps like ERPNext yet"
echo "on purpose — install ERPNext (or anything else) from the Apps tab"
echo "in the dashboard itself, with one click."
echo ""
echo "From here on, everything else — installing apps, backups, new"
echo "sites — is done from the browser, not the command line."
