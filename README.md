# Central Control Plane

A GitOps-based Kubernetes cluster management system that provides centralized provisioning and lifecycle management for multiple clusters across regions and sectors.

## Overview

This system enables:
- **Progressive delivery** across sectors, regions, and individual clusters
- **Pluggable pipeline tasks** for different cloud providers
- **Hierarchical configuration** with inheritance from defaults → sectors → regions → clusters
- **GitOps workflow** using ArgoCD for declarative cluster management
- **Cross-repository modularity** for pipeline tasks and provisioning templates

### Cluster Management Pipeline

Each cluster is managed through a three-stage pipeline:
- **Pre-provision**: Setup tasks before cluster creation
- **Provision**: Actual cluster provisioning using cloud-specific resources
- **Post-provision**: Configuration and validation after cluster creation

All tasks MUST be **idempotent** and can be selectively enabled/disabled.

## Project Structure

```
.
├── values.yaml                                    # Main configuration file
├── central-control-plane-applications/            # ArgoCD Applications
│   ├── central-control-plane-pipelines.application.yaml
│   └── cluster-configs.application.yaml
├── central-control-plane/                         # Core components
│   ├── cluster-configs/                           # Generates cluster ConfigMaps
│   ├── pipelines/                                 # Tekton pipeline definitions
│   └── pipelinerun-trigger/                       # PipelineRun trigger chart
└── providers/                                     # Provider-specific implementations
    ├── aws/                                       # AWS provider
    │   ├── provision-application/                 # ArgoCD app for provisioning
    │   ├── provision/                             # Helm chart for AWS resources
    │   └── pipeline-tasks/                        # AWS-specific tasks
    │       ├── pre.yaml
    │       ├── provision.yaml
    │       └── post.yaml
    └── <other-providers>/                         # Additional providers
```

## Configuration System

### Hierarchical Configuration (`values.yaml`)

The configuration follows a hierarchical inheritance model:

```
cluster config → region config → sector config → defaults
```

### Configuration Sections

- **`defaults`**: Base configuration for all clusters
- **`sectors`**: Environment-specific defaults (canary, prod-01, prod-02)
- **`regions`**: Geographic defaults with sector mapping
- **`clusters`**: Individual cluster configurations

### Example Configuration Structure

```yaml
defaults:
  tasks: ...
  data:
    WORKER_MACHINE_TYPE: "m5.xlarge"
    # ... other defaults

sectors:
  canary:
    tasks: ...
    data:
      KUBERNETES_VERSION: "1.33"
      WORKER_MACHINE_COUNT: "2"
  prod-01:
    tasks: ...
    data:
      KUBERNETES_VERSION: "1.29"
      WORKER_MACHINE_COUNT: "6"

regions:
  eu-west-1:
    sector: canary
    tasks: ...
    data:
      REGION: "eu-west-1"

clusters:
  cluster-01:
    region: eu-west-1
    tasks: ...
    data:
      ROLE_ARN: "arn:aws:iam::100000000001:role/central-control-plane"
```

## Getting Started

### Prerequisites

- `kind` - For local development cluster
- `kubectl` - Kubernetes CLI
- `helm` - Helm package manager

### Development Setup

1. **Create local cluster**:
   ```bash
   kind create cluster --name central-control-plane
   ```

2. **Install ArgoCD**:
   ```bash
   kubectl create namespace argocd
   kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
   ```

3. **Install Tekton**:
   ```bash
   kubectl create namespace tekton-pipelines
   kubectl apply --filename https://storage.googleapis.com/tekton-releases/pipeline/latest/release.yaml
   ```

4. **Install Tekton Dashboard** (optional):
   ```bash
   kubectl apply --filename https://storage.googleapis.com/tekton-releases/dashboard/latest/release-full.yaml
   ```

### Access Services

Set up port-forwarding for local access:

```bash
# ArgoCD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
kubectl port-forward svc/argocd-server -n argocd 8080:80

# Tekton Dashboard
kubectl port-forward svc/tekton-dashboard -n tekton-pipelines 9097:9097
```

Get ArgoCD admin password:
```bash
kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}" | base64 -d
```

## Usage

### 1. Configure Clusters

Edit `values.yaml` to define your clusters, regions, and sectors according to your infrastructure needs.

Validate your configuration:
```bash
helm template central-control-plane/cluster-configs
```

### 2. Deploy Control Plane

Install the ArgoCD applications that manage cluster configurations and pipelines:

```bash
kubectl apply -f central-control-plane-applications/
```

This creates:
- Cluster ConfigMaps for each defined cluster
- The cluster management pipeline

Verify installation:
```bash
# Check ConfigMaps
kubectl get configmaps -n default
NAME                   DATA   AGE
cluster-01-configmap   11     4s
cluster-02-configmap   11     4s
cluster-03-configmap   11     4s
cluster-04-configmap   11     4s
...

# Check pipelines
kubectl get pipelines
NAME                 AGE
cluster-management   14s
```

### 3. Provision a Cluster

Trigger cluster provisioning using the PipelineRun trigger:

```bash
helm template central-control-plane/pipelinerun-trigger \
  --set cluster-name=cluster-01 | kubectl create -f -
```

#### Selective Task Execution

You can disable specific pipeline stages:

```bash
# Skip post-provision tasks
helm template central-control-plane/pipelinerun-trigger \
  --set cluster-name=cluster-01 \
  --set run-post=false | kubectl create -f -

# Run only pre-provision tasks
helm template central-control-plane/pipelinerun-trigger \
  --set cluster-name=cluster-01 \
  --set run-provision=false \
  --set run-post=false | kubectl create -f -
```

### 4. Monitor Progress

Track pipeline execution:

```bash
# List PipelineRuns
kubectl get pipelineruns

# Get detailed status
kubectl describe pipelinerun <pipelinerun-name>

# Follow logs
kubectl logs -f <pod-name>
```

## Extending the System

### Adding New Providers

1. Create provider directory: `providers/<provider-name>/`
2. Implement the three required tasks:
   - `pipeline-tasks/pre.yaml`
   - `pipeline-tasks/provision.yaml`
   - `pipeline-tasks/post.yaml`
3. Create provision templates:
   - `provision-application/` - ArgoCD application chart
   - `provision/` - Provider-specific resource definitions
4. Update task references in `values.yaml`

Note that these tasks can be defined in an external repository.

### Customizing Pipeline Tasks

Tasks are dynamically loaded from Git repositories and can be customized at any level of the configuration hierarchy. The system supports:

- **Different repositories** for different environments or providers
- **Version pinning** using Git revisions for stability
- **Path customization** to organize tasks within repositories
- **Per-environment overrides** for progressive delivery

#### Task Configuration Parameters

Each task stage (`pre`, `provision`, `post`) uses three parameters:
- `{stage}-task-git-url`: Git repository URL
- `{stage}-task-path`: Path to the task YAML file within the repository
- `{stage}-task-revision`: Git revision (branch, tag, or commit SHA)

These parameters should be defined in the `defaults` section of `values.yaml`, but can be overridden at the sector, region and cluster level, e.g.:

```yaml
sectors:
  canary:
    tasks:
      provision-task-git-url: "https://github.com/myorg/canary-tasks.git"
      provision-task-revision: "v2.0.0-beta"
      provision-task-path: "aws/experimental/provision.yaml"
      ...
```

This hierarchical task configuration enables fine-grained control over which task versions run in different environments while maintaining consistency where needed.
