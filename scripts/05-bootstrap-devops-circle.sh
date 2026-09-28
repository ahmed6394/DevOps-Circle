#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-}"
BRANCH="${BRANCH:-main}"

if [[ -z "$REPO_URL" ]]; then
  echo "Usage: REPO_URL=https://github.com/<org>/<repo>.git ./scripts/05-bootstrap-devops-circle.sh"
  exit 1
fi

TMP_FILE="/tmp/devops-circle-argocd-application.yaml"
cp k8s/argocd/devops-circle-application.yaml "$TMP_FILE"
sed -i "s#https://github.com/ahmed6394/DevOps-Circle.git#${REPO_URL}#g" "$TMP_FILE"
sed -i "s#targetRevision: main#targetRevision: ${BRANCH}#g" "$TMP_FILE"

kubectl apply -f "$TMP_FILE"
kubectl -n argocd get applications
printf '\nArgoCD will now sync DevOps Circle from: %s\n' "$REPO_URL"
