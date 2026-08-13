#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR=/opt/lanran-site
WEB_ROOT=/usr/local/lighthouse/softwares/wordpress
STATE_FILE=/var/lib/lanran-site/wordpress-state.sha256
WORDPRESS_API=http://43.132.148.205/wp-json/wp/v2/posts

exec 9>/var/lock/lanran-site-deploy.lock
flock -n 9 || exit 0

mkdir -p "$(dirname "$STATE_FILE")"
new_state=$(curl -fsS "$WORDPRESS_API?per_page=100&orderby=modified&order=desc&_fields=id,modified,status" | sha256sum | awk '{print $1}')
old_state=$(cat "$STATE_FILE" 2>/dev/null || true)

if [[ "${1:-}" != "--force" && "$new_state" == "$old_state" ]]; then
  exit 0
fi

cd "$SOURCE_DIR"
export ASTRO_TELEMETRY_DISABLED=1
export PUBLIC_WORDPRESS_URL=http://43.132.148.205
export PUBLIC_SITE_URL=http://43.132.148.205
export PUBLIC_BASE_PATH=/

pnpm run build
cp -a dist/. "$WEB_ROOT/"

/www/server/nginx/sbin/nginx -t -c /www/server/nginx/conf/nginx.conf
/www/server/nginx/sbin/nginx -s reload
printf '%s\n' "$new_state" > "$STATE_FILE"
printf '%s Site updated from WordPress.\n' "$(date '+%F %T')"
