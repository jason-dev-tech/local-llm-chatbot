#!/bin/sh
set -eu

API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8001}"
ESCAPED_API_BASE_URL=$(
  printf '%s' "$API_BASE_URL" | sed \
    -e 's/\\/\\\\/g' \
    -e 's/"/\\"/g'
)

cat <<EOF >/usr/share/nginx/html/runtime-config.js
window.__APP_CONFIG__ = {
  apiBaseUrl: "${ESCAPED_API_BASE_URL}"
};
EOF
