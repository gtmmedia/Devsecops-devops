#!/usr/bin/env bash
# One-shot cluster setup AFTER `terraform apply` and `aws eks update-kubeconfig`.
# Installs: namespace -> ingress-nginx -> Prometheus + Grafana -> QuickDesk (Helm).
#
# Usage:
#   GITHUB_OWNER=your-github-username IMAGE_TAG=<full git sha> ./scripts/bootstrap-cluster.sh
set -euo pipefail

: "${GITHUB_OWNER:?Set GITHUB_OWNER to your GitHub username (lowercase)}"
: "${IMAGE_TAG:?Set IMAGE_TAG to the Git SHA your pipeline pushed (see the GHCR package page)}"
NAMESPACE="${NAMESPACE:-quickdesk}"
cd "$(dirname "$0")/.."

echo "==> Cluster check"
kubectl get nodes

echo "==> Namespace"
kubectl apply -f k8s/namespace.yaml

echo "==> Helm repos"
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx >/dev/null 2>&1 || true
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null 2>&1 || true
helm repo update >/dev/null

echo "==> Ingress controller"
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace \
  -f k8s/ingress-nginx-values.yaml --wait --timeout 8m

echo "==> Prometheus + Grafana (installed BEFORE the app so the ServiceMonitor CRD exists)"
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  -f monitoring/prometheus-values.yaml -f monitoring/grafana-values.yaml \
  --wait --timeout 10m

echo "==> QuickDesk"
helm upgrade --install quickdesk helm/quickdesk \
  --namespace "$NAMESPACE" --create-namespace \
  --set backend.image.repository="ghcr.io/${GITHUB_OWNER}/quickdesk-backend" \
  --set backend.image.tag="$IMAGE_TAG" \
  --set frontend.image.repository="ghcr.io/${GITHUB_OWNER}/quickdesk-frontend" \
  --set frontend.image.tag="$IMAGE_TAG" \
  --wait --timeout 8m

echo
kubectl get pods,svc,ingress,hpa -n "$NAMESPACE"
echo
echo "Load balancer address (can take 2-3 minutes to resolve in DNS):"
kubectl get svc -n ingress-nginx ingress-nginx-controller \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}{"\n"}'
echo
echo "Grafana password:"
kubectl get secret -n monitoring monitoring-grafana -o jsonpath='{.data.admin-password}' | base64 -d; echo
