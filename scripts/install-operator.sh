#!/usr/bin/env bash
set -euo pipefail

OPERATOR_VERSION="1.3.0"

echo "Adding KubeRay Helm repository..."
helm repo add kuberay https://ray-project.github.io/kuberay-helm/
helm repo update

echo "Installing KubeRay Operator v${OPERATOR_VERSION}..."
helm upgrade --install kuberay-operator kuberay/kuberay-operator \
  --version "${OPERATOR_VERSION}" \
  --namespace kuberay-system --create-namespace \
  --set resources.requests.cpu=100m \
  --set resources.requests.memory=512Mi \
  --set resources.limits.memory=512Mi \
  --wait

echo "Creating target namespace ray-system..."
kubectl create namespace ray-system --dry-run=client -o yaml | kubectl apply -f -

echo "Verifying KubeRay CRDs..."
kubectl get crd rayclusters.ray.io rayjobs.ray.io rayservices.ray.io

echo "KubeRay Operator installation verified successfully!"
