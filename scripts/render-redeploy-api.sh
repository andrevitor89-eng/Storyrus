#!/usr/bin/env bash
# Redeploy storyrus-api no Render via API.
# Uso:
#   export RENDER_API_KEY=rnd_...
#   ./scripts/render-redeploy-api.sh
set -euo pipefail

SERVICE_ID="${RENDER_SERVICE_ID:-srv-d98gm9taeets73fuarug}"
API_KEY="${RENDER_API_KEY:?Defina RENDER_API_KEY (Account → API Keys no Render)}"

echo "Trigger clearCache deploy for $SERVICE_ID ..."
curl -sS -X POST "https://api.render.com/v1/services/${SERVICE_ID}/deploys" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"clearCache":"clear"}'
echo
echo "Acompanhe: https://dashboard.render.com/web/${SERVICE_ID}"
