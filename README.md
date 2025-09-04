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

## Cluster Configuration

The main configuration file where the clusters are defined is `values.yaml`

It has the following sections:
- `defaults`: defaults for all clusters
- `sectors`: defaults per sector
- `regions`: defaults per region and mapping to sector
- `clusters`: clusters with their data

For each section, the `data` key is used to set the data for the cluster, and the `tasks` key is used to dynamically fetch the pipeline tasks for the cluster and to enable them selectively.

The precedence of the data is: `cluster` -> `region` -> `sector` -> `defaults`.

## Design

Each cluster is provisioned and lifecycled using the `pipelines/cluster-management.pipeline.yaml` pipeline. This pipeline uses a configmap for each cluster to store the cluster configuration. The configmap is generated using the `values.yaml` file, and the applied to the cluster using the `cluster-configs/cluster-configs.application.yaml` ArgoCD Application.

Each pipeline has three tasks:
- `pre-task`: runs before the provision task
- `provision-task`: provisions the cluster
- `post-task`: runs after the provision task

Note that all tasks MUST be idempotent.

These tasks are dynamically fetched from the `values.yaml` file, and the `tasks` key is used to set the pipeline tasks for the cluster, using the following parameters:
- `pre-task-git-url`: Git URL for pre-provision task
- `pre-task-path`: Path to pre-provision task in git repo
- `pre-task-revision`: Git revision for pre-provision task
- `provision-task-git-url`: Git URL for provision task
- `provision-task-path`: Path to provision task in git repo
- `provision-task-revision`: Git revision for provision task
- `post-task-git-url`: Git URL for post-provision task
- `post-task-path`: Path to post-provision task in git repo
- `post-task-revision`: Git revision for post-provision task
- `run-pre`: Whether to run the pre-provision task (true/false)
- `run-provision`: Whether to run the provision task (true/false)
- `run-post`: Whether to run the post-provision task (true/false)

In order to trigger the pipeline, the `PipelineRun` should include the above attributes, and a reference to the cluster configuration configmap.

The provision task works as follows:
1. Clone the provision templates repository (url, path and revision should be defined in `values.yaml`). This repository includes a helm chart of the ArgoCD Application to be applied to the cluster, which will in turn apply the CRs required to provision the cluster (stored as another helm chart in the same repository).
2. Generate the ArgoCD Application using Helm (helm template). It will include the cluster configuration as values passed through the `helm` CLI. These parameters are stored in the configmap referenced by the pipeline run.
3. ArgoCD applies the helm chart of the CRs required to provision the cluster
4. Wait for the Application to be synced

Since the provision task is specific to the provider, it can be customized for each provider. In particular, it can be applied from a repo referenced in the `values.yaml` file (repourl, path and revision can be defined in `values.yaml`).

This enables progressive delivery across sectors, regions and clusters.

## Usage

### Cluster Configmaps

Begin by filling in the `values.yaml` file with the cluster configuration.

Then, apply the cluster configmaps ArgoCD Application:

```bash
kubectl apply -f cluster-configs/cluster-configs.application.yaml
```
