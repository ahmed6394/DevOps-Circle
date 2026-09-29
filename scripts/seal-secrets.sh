#!/usr/bin/env bash
set -euo pipefail

# Regenerates k8s/base/11-sealed-secret.yaml from local .env values.
# Requires: kubectl, kubeseal, and the Sealed Secrets controller running.
# Set the controller name/namespace to match your install.

CONTROLLER_NAME="${SEALED_SECRETS_CONTROLLER:-sealed-secrets-controller}"
CONTROLLER_NAMESPACE="${SEALED_SECRETS_NAMESPACE:-sealed-secrets}"

[[ -f .env ]] || { echo "Missing .env"; exit 1; }
set -a; source .env; set +a

: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD required}"
: "${DATABASE_URL:?DATABASE_URL required}"
: "${JWT_SECRET:?JWT_SECRET required}"

TMP_FILE="$(mktemp)"
trap 'rm -f "$TMP_FILE"' EXIT

cat > "$TMP_FILE" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: devops-circle-secret
  namespace: devops-circle
type: Opaque
stringData:
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
  DATABASE_URL: ${DATABASE_URL}
  JWT_SECRET: ${JWT_SECRET}
EOF

kubeseal --controller-name "$CONTROLLER_NAME" --controller-namespace "$CONTROLLER_NAMESPACE" \
  --format yaml < "$TMP_FILE" > k8s/base/11-sealed-secret.yaml

printf 'Wrote k8s/base/11-sealed-secret.yaml\n'