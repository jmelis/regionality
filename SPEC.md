# Regionality Implementation Spec

## Overview
Create a hierarchical Kustomize structure for ArgoCD Applications that manages cluster configurations with sector → region → cluster inheritance. Each cluster gets a ConfigMap with its name and git commit SHA for deployment.

## Repository Details
- **Repository**: https://github.com/jmelis/regionality
- **Structure**: Kustomize overlays with three-tier hierarchy
- **Purpose**: Manage cluster configurations with flexible sector assignment per region

## Directory Structure to Create

```
├── base/
│   ├── configmap.yaml
│   └── kustomization.yaml
├── overlays/
│   ├── sectors/
│   │   ├── canary/
│   │   │   ├── kustomization.yaml
│   │   │   └── configmap-patch.yaml
│   │   ├── stage/
│   │   │   ├── kustomization.yaml
│   │   │   └── configmap-patch.yaml
│   │   ├── prod-0/
│   │   │   ├── kustomization.yaml
│   │   │   └── configmap-patch.yaml
│   │   └── prod-1/
│   │       ├── kustomization.yaml
│   │       └── configmap-patch.yaml
│   ├── regions/
│   │   ├── us-east/
│   │   │   ├── kustomization.yaml
│   │   │   └── configmap-patch.yaml
│   │   ├── us-west/
│   │   │   ├── kustomization.yaml
│   │   │   └── configmap-patch.yaml
│   │   ├── eu-west/
│   │   │   ├── kustomization.yaml
│   │   │   └── configmap-patch.yaml
│   │   └── ap-south/
│   │       ├── kustomization.yaml
│   │       └── configmap-patch.yaml
│   └── clusters/
│       ├── regional-cluster-us-east/
│       │   ├── kustomization.yaml
│       │   └── configmap-patch.yaml
│       ├── regional-access-cluster-us-east/
│       │   ├── kustomization.yaml
│       │   └── configmap-patch.yaml
│       ├── regional-cluster-us-west/
│       │   ├── kustomization.yaml
│       │   └── configmap-patch.yaml
│       ├── regional-access-cluster-us-west/
│       │   ├── kustomization.yaml
│       │   └── configmap-patch.yaml
│       ├── regional-cluster-eu-west/
│       │   ├── kustomization.yaml
│       │   └── configmap-patch.yaml
│       ├── regional-access-cluster-eu-west/
│       │   ├── kustomization.yaml
│       │   └── configmap-patch.yaml
│       ├── regional-cluster-ap-south/
│       │   ├── kustomization.yaml
│       │   └── configmap-patch.yaml
│       └── regional-access-cluster-ap-south/
│           ├── kustomization.yaml
│           └── configmap-patch.yaml
├── argocd/
│   └── applications/
└── README.md
```

## File Contents Specifications

### Base Configuration

**base/configmap.yaml:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-config
  namespace: default
data:
  cluster_name: "default-cluster"
  commit: "main"
```

**base/kustomization.yaml:**
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- configmap.yaml
```

### Sector Configurations

Create each sector with appropriate commit values:

**overlays/sectors/canary/kustomization.yaml:**
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- ../../../base

patches:
- path: configmap-patch.yaml
```

**overlays/sectors/canary/configmap-patch.yaml:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-config
data:
  commit: "canary-latest"
```

**Sector commit mappings:**
- canary: `"canary-latest"`
- stage: `"stage-v2.3.0-rc1"`
- prod-0: `"prod-v2.2.5"`
- prod-1: `"prod-v2.3.0"`

### Region Configurations

Each region should inherit from a sector and optionally override the commit:

**overlays/regions/us-east/kustomization.yaml:**
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- ../../sectors/prod-0

patches:
- path: configmap-patch.yaml
```

**overlays/regions/us-east/configmap-patch.yaml:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-config
data:
  commit: "prod-v2.2.5-us-east-patch"
```

**Default sector assignments:**
- us-east → prod-0
- us-west → stage  
- eu-west → prod-1
- ap-south → canary

### Cluster Configurations

Each cluster inherits from its region and sets cluster_name:

**overlays/clusters/regional-cluster-us-east/kustomization.yaml:**
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- ../../regions/us-east

patches:
- path: configmap-patch.yaml
```

**overlays/clusters/regional-cluster-us-east/configmap-patch.yaml:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-config
data:
  cluster_name: "regional-cluster-us-east"
```

**Cluster naming pattern:**
- `regional-cluster-{region}`
- `regional-access-cluster-{region}`

### ArgoCD Applications

Create sample ArgoCD applications in `argocd/applications/`:

**argocd/applications/regional-cluster-us-east.yaml:**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: cluster-config-regional-cluster-us-east
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/jmelis/regionality
    targetRevision: head
    path: overlays/clusters/regional-cluster-us-east
  destination:
    server: https://regional-cluster-us-east.k8s.local
    namespace: default
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

Create applications for all 8 clusters (2 per region × 4 regions).

## Implementation Requirements

1. **File Creation**: Create all files exactly as specified in the directory structure
2. **Consistent Naming**: Use lowercase throughout, follow naming patterns strictly
3. **Inheritance Chain**: Ensure sector → region → cluster inheritance works correctly
4. **Validation**: Each cluster should produce a valid ConfigMap when processed by Kustomize
5. **Documentation**: Include a comprehensive README.md explaining:
   - Directory structure and inheritance
   - How to change sector assignments
   - How to add new regions/clusters
   - ArgoCD integration instructions

## Key Features to Implement

1. **Flexible Sector Assignment**: Regions can be reassigned to different sectors by changing one line
2. **Standardized Clusters**: Each region has exactly two clusters with predictable names
3. **Override Hierarchy**: Support overrides at sector, region, and cluster levels
4. **ArgoCD Ready**: Include complete ArgoCD Application manifests

## Testing Verification

After implementation, verify that:
1. `kustomize build overlays/clusters/regional-cluster-us-west-2` produces valid YAML
2. `kustomize build overlays/clusters/regional-access-cluster-frm-us-east-1` produces valid YAML
3. Each cluster produces correct cluster_name and commit values
4. Changing a region's sector assignment affects both its clusters
5. All ArgoCD applications reference correct paths and repositories

## Success Criteria

- All 25+ files created correctly
- Kustomize builds work for all cluster overlays  
- Clear inheritance hierarchy is maintained
- ArgoCD applications are ready for deployment
- Documentation explains usage and maintenance
