# README

## Requirements

CLI tools:
- `kind`
- `kubectl`
- `helm`
- `tkn`

## Development setup

```bash
# Install kind cluster
kind create cluster --name central-control-plane

# Install argocd
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Install tekton
kubectl create namespace tekton-pipelines
kubectl apply --filename https://storage.googleapis.com/tekton-releases/pipeline/latest/release.yaml

# Install tekton dashboard
kubectl apply --filename https://storage.googleapis.com/tekton-releases/dashboard/latest/release-full.yaml
```

Set up port-forwarding:
- `kubectl port-forward svc/argocd-server -n argocd 8080:443`
- `kubectl port-forward svc/tekton-dashboard -n tekton-pipelines 9097:9097`

Get the ArgoCD admin password:
```bash
kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}" | base64 -d
```
