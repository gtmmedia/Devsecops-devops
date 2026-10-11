#!/usr/bin/env bash
# Remove everything Kubernetes created in AWS, THEN run `terraform destroy`.
#
# Why the order matters: the ingress controller creates a load balancer and
# PostgreSQL creates an EBS disk. Terraform doesn't know about them, so
# `terraform destroy` would hang or fail trying to delete the VPC they live in.
set -euo pipefail
NAMESPACE="${NAMESPACE:-quickdesk}"

echo "==> Removing the app"
helm uninstall quickdesk -n "$NAMESPACE" || true
# StatefulSet volumes are NOT deleted by helm uninstall - delete them explicitly.
kubectl delete pvc --all -n "$NAMESPACE" --ignore-not-found

echo "==> Removing monitoring"
helm uninstall monitoring -n monitoring || true
kubectl delete pvc --all -n monitoring --ignore-not-found

echo "==> Removing the ingress controller (this deletes the AWS load balancer)"
helm uninstall ingress-nginx -n ingress-nginx || true
kubectl delete namespace "$NAMESPACE" monitoring ingress-nginx --ignore-not-found --wait=true

echo "==> Giving AWS a minute to finish deleting the load balancer and disks"
sleep 90

echo
echo "Now run:   cd terraform && terraform destroy"
echo "Then check the AWS console (EC2 > Load Balancers, EC2 > Volumes, VPC) is empty."
