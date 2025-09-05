# README

## Project structure

```bash
.
├── values.yaml # Cluster information (with inheritance from region, sector and defaults)
├── central-control-plane-applications
│   ├── central-control-plane-pipelines.application.yaml # ArgoCD Application that install pipelines helm chart
│   └── cluster-configs.application.yaml # ArgoCD Application that install cluster-configs helm chart
├── central-control-plane
│   ├── cluster-configs # Helm chart that renders the cluster configmaps from the `values.yaml` file
│   ├── pipelines # Helm chart that renders the pluggable pipeline from the `values.yaml` file
│   └── pipelinerun-trigger # Helm chart that creates the PipelineRun for the cluster
└── providers
    ├── aws # AWS specific tasks and provision templates
    │   ├── provision-application # ArgoCD Application that install the provision templates helm chart
    │   ├── provision # Helm chart that renders the provision templates from the `values.yaml` file
    │   ├── pipeline-tasks # Providers specific pipeline tasks
    │   │   ├── post.yaml
    │   │   ├── pre.yaml
    │   │   └── provision.yaml
    ├── <another provider e.g. azure, gcp, etc.>
    │   └── ...
    └── ...
```

## Development setup

Required CLI tools:
- `kind`
- `kubectl`
- `helm`

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

## Cluster Configuration (`values.yaml`)

The main configuration file where the clusters are defined is `values.yaml`.

It has the following sections:
- `defaults`: defaults for all clusters
- `sectors`: defaults per sector
- `regions`: defaults per region and mapping to sector
- `clusters`: clusters with their data

For each section, the `data` key is used to set the data for the cluster, and the `tasks` key is used to dynamically fetch the pipeline tasks for the cluster and to enable them selectively.

The `data` section will include the necessary data for the Pipeline tasks to execute, it should include things such as:
- Cluster version
- Node type
- Number of nodes
- Cloud account ID (if applicable)

The precedence of the data is: `cluster` -> `region` -> `sector` -> `defaults`. Ideally the cluster stanzas should be kept to a minimum, and the data should be inherited from the default, region and sector stanzas.

The reasoning behind this inheritance system is in order to enable progressive delivery across sectors, regions and clusters, and to keep clusters as similar as possible within the same region or sector.

The `central-control-plane/cluster-configs` helm chart is then used to generate a configmap for each cluster.

## Cluster Management Pipeline and Provider Tasks

Each cluster is provisioned and lifecycled using the `central-control-plane/pipelines/cluster-management.pipeline.yaml` pipeline. This pipeline relies on a configmap for each cluster to store the cluster configuration. The configmap is generated using the `values.yaml` file, and the applied to the cluster using the `cluster-configs/cluster-configs.application.yaml` ArgoCD Application.

The Cluster Management Pipeline has exactly three tasks:
- `pre`: runs before the provision task
- `provision`: provisions the cluster
- `post`: runs after the provision task

Note that all tasks MUST be idempotent.

Each task can load the cluster configuration configmap using the regular mechanisms: either as an environment variable and/or as a volume mount.

All tasks are dynamically fetched from the `values.yaml` file, using the following parameters:
- `pre-task-git-url`: Git URL for pre-provision task
- `pre-task-path`: Path to pre-provision task in git repo
- `pre-task-revision`: Git revision for pre-provision task
- `provision-task-git-url`: Git URL for provision task
- `provision-task-path`: Path to provision task in git repo
- `provision-task-revision`: Git revision for provision task
- `post-task-git-url`: Git URL for post-provision task
- `post-task-path`: Path to post-provision task in git repo
- `post-task-revision`: Git revision for post-provision task

This enables cross-repository pluggability of the pipeline tasks.

### Provision Task

The provision task works as follows:
1. Clone the provision templates repository (url, path and revision should be defined in `values.yaml`). This repository includes a helm chart of the ArgoCD Application to be applied to the cluster, which will in turn apply the CRs required to provision the cluster (stored as another helm chart in the same repository).
2. Generate the ArgoCD Application using Helm (helm template). It will include the cluster configuration as values passed through the `helm` CLI. These parameters are stored in the configmap referenced by the pipeline run.
3. ArgoCD applies the helm chart of the CRs required to provision the cluster
4. Wait for the Application to be synced

Since the provision task is specific to the provider, it can be customized for each provider. In particular, it can be applied from a repo referenced in the `values.yaml` file (repourl, path and revision can be defined in `values.yaml`).

This enables progressive delivery across sectors, regions and clusters.

In the particular example implementation, the url of the repository cloned is obtained from the following parameters defined in `values.yaml`:
- `PROVISION_REPO`
- `PROVISION_REVISION`
- `PROVISION_APPLICATION_PATH`
- `PROVISION_PATH`

## Usage

### `values.yaml`

Fill in the `values.yaml` file with the cluster configuration.

Verify the rendered configmaps:

```bash
helm template central-control-plane/cluster-configs
```

### Install Cluster Configmaps and Pipelines ArgoCD Applications

```bash
kubectl apply -f central-control-plane-applications/
```

This should install the cluster configmaps, e.g.:

```bash
kubectl get configmaps -n default
NAME                   DATA   AGE
cluster-01-configmap   7      69s
cluster-02-configmap   7      69s
cluster-03-configmap   6      69s
...
```

And the pipelines:

```bash
kubectl get pipelines
NAME                 AGE
cluster-management   2m52s
```

### Lifecycle a Cluster

A `PipelineRun` can be triggered by using the `pipelinerun-trigger` chart.

```bash
helm template central-control-plane/pipelinerun-trigger --set cluster-name=cluster-01 | kubectl create -f -
```

The `cluster-name` parameter is mandatory.

Note that tasks can be disabled by setting the `run-pre`, `run-provision` and `run-post` parameters to `false`, e.g.:

```bash
helm template central-control-plane/pipelinerun-trigger --set cluster-name=cluster-01 --set run-post=false --set run-provision=false | kubectl create -f -
```
