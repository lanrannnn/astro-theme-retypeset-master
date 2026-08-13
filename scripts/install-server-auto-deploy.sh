#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR=/opt/lanran-site
SYNC_SCRIPT=/usr/local/bin/lanran-site-sync
CRON_FILE=/etc/cron.d/lanran-site-sync

if [[ $(id -u) -ne 0 ]]; then
  echo "Run this installer as root." >&2
  exit 1
fi

if ! command -v node >/dev/null 2>&1 || [[ $(node -p 'Number(process.versions.node.split(".")[0])') -lt 22 ]]; then
  curl -fsSL https://rpm.nodesource.com/setup_22.x | bash -
  dnf install -y nodejs
fi

if ! command -v pnpm >/dev/null 2>&1; then
  npm install -g pnpm@10.33.0
fi

cd "$SOURCE_DIR"
pnpm install --frozen-lockfile

install -m 0755 "$SOURCE_DIR/scripts/server-auto-deploy.sh" "$SYNC_SCRIPT"
cat > "$CRON_FILE" <<'EOF'
*/5 * * * * root /usr/local/bin/lanran-site-sync >> /var/log/lanran-site-sync.log 2>&1
EOF
chmod 0644 "$CRON_FILE"

"$SYNC_SCRIPT" --force
echo "Automatic WordPress deployment is installed and runs every 5 minutes."
