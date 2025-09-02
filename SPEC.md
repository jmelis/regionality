# Regionality - Claude Code Implementation Spec

## Project Overview
Create a GitOps repository called "regionality" for CAPI cluster provisioning with Tekton pipelines and ArgoCD. This implementation focuses **only on AWS EKS clusters in the frm-poc region**.

## Scope - Initial Implementation
- **Provider**: AWS EKS only
- **Region**: frm-poc only  
- **Cluster**: Single cluster (aws-cluster-01)
- **Authentication**: STS cross-account role assumption from ROSA HCP

## Repository Structure to Implement

```
regionality/
├── README.md
├── bootstrap/
│   └── argocd/
│       ├── app-of-apps.yaml
│       └── applications/
│           ├── tekton-pipelines.yaml
│           └── cluster-provisioning.yaml
├── tekton/
│   ├── base/
│   │   ├── kustomization.yaml
│   │   ├── pipeline.yaml
│   │   ├── task-assume-role.yaml
│   │   ├── task-provision-cluster.yaml
│   │   └── rbac.yaml
│   └── overlays/
│       ├── regions/
│       │   └── frm-poc/
│       │       ├── kustomization.yaml
│       │       └── region-config.yaml
│       └── clusters/
│           └── frm-poc/
│               └── aws-cluster-01/
│                   ├── kustomization.yaml
│                   └── cluster-config.yaml
├── clusters/
│   ├── base/
│   │   ├── kustomization.yaml
│   │   └── aws/
│   │       └── cluster-template.yaml
│   └── frm-poc/
│       └── aws-cluster-01/
│           ├── kustomization.yaml
│           └── cluster.yaml
└── config/
    ├── credentials/
    │   └── aws/
    │       └── sts-roles/
    │           └── frm-poc-account-role.yaml
    └── accounts/
        └── aws/
            └── frm-poc-shared.yaml
```

## Implementation Requirements - MINIMAL PROOF OF CONCEPT

**CRITICAL: Keep all files to the absolute bare minimum for functionality. This is a proof of concept, not production-ready. Only include what's strictly necessary to make it work.**

### File Content Guidelines
- **Short files**: Each YAML file should be as concise as possible
- **Minimal configuration**: Only essential parameters and settings
- **No extras**: Remove any optional fields, comments, or advanced features
- **Proof of concept**: Focus on demonstrating the flow works, not completeness
- **Essential only**: If it's not required for the basic flow to function, don't include it

### 1. Bootstrap Components - MINIMAL
- **app-of-apps.yaml**: Basic ArgoCD application, minimal config
- **tekton-pipelines.yaml**: Basic ArgoCD application for Tekton, minimal config
- **cluster-provisioning.yaml**: Basic ArgoCD application for cluster provisioning, minimal config

### 2. Tekton Pipeline Components - MINIMAL

#### Base Pipeline (tekton/base/) - ESSENTIAL ONLY
- **pipeline.yaml**: Two tasks only, minimal parameters:
  1. assume-role task
  2. provision-cluster task
- **task-assume-role.yaml**: Bare minimum STS assume role, essential steps only
- **task-provision-cluster.yaml**: Basic CAPI apply, essential steps only
- **rbac.yaml**: Minimal RBAC, only what's needed for pipeline to run
- **kustomization.yaml**: Basic kustomize, no extras

#### Region Overlay (tekton/overlays/regions/frm-poc/) - MINIMAL
- **region-config.yaml**: Only essential region parameters
- **kustomization.yaml**: Basic reference to base, minimal patches

#### Cluster Overlay (tekton/overlays/clusters/frm-poc/aws-cluster-01/) - MINIMAL  
- **cluster-config.yaml**: Only cluster name and role ARN
- **kustomization.yaml**: Basic reference, minimal patches

### 3. CAPI Cluster Definitions - MINIMAL

#### Base Template (clusters/base/aws/) - ESSENTIAL ONLY
- **cluster-template.yaml**: Most basic CAPI cluster template that works

#### Specific Cluster (clusters/frm-poc/aws-cluster-01/) - MINIMAL
- **cluster.yaml**: Simplest working CAPI cluster definition
- **kustomization.yaml**: Basic base reference

### 4. Configuration - MINIMAL

#### AWS STS Role Configuration - ESSENTIAL ONLY
- **frm-poc-account-role.yaml**: Just the role ARN, nothing else
- **frm-poc-shared.yaml**: Just account ID, minimal fields

## Technical Requirements

### Pipeline Functionality - MINIMAL IMPLEMENTATION
1. **assume-role task**:
   - Accept target-role-arn parameter only
   - Basic `aws sts assume-role` call
   - Output credentials (access key, secret key, session token)
   - No error handling, no fancy features

2. **provision-cluster task**:
   - Accept cluster name, config path, and credentials
   - Basic `kubectl apply -k` command
   - Simple cluster wait
   - No advanced monitoring or validation

### CAPI Integration - MINIMAL
- Basic AWS CAPI provider usage
- Simplest EKS cluster that can be created
- Default settings wherever possible
- No custom networking, security groups, etc.

### Kustomize Usage - MINIMAL
- Basic base + overlay pattern
- Only essential parameter substitution
- No complex transformations

### ArgoCD Integration - MINIMAL
- Basic app-of-apps
- Simple sync policies
- Default namespaces where possible

## Key Parameters to Expose
- **cluster-name**: aws-cluster-01
- **region**: frm-poc  
- **target-role-arn**: AWS role ARN to assume for provisioning
- **cluster-config-path**: Path to cluster kustomization (clusters/frm-poc/aws-cluster-01)

## Success Criteria - PROOF OF CONCEPT
1. Repository structure exists and is minimal
2. ArgoCD can bootstrap (doesn't need to be perfect)
3. Tekton pipeline can assume AWS role (basic functionality)
4. Pipeline can attempt to provision EKS cluster via CAPI
5. Kustomizations are syntactically correct
6. **All files are SHORT and contain only essential elements**

## CRITICAL IMPLEMENTATION NOTES
- **Every file should be under 50 lines if possible**
- **Remove all optional YAML fields**
- **Use defaults wherever possible**
- **No comments or documentation in YAML files**
- **No advanced features or edge case handling**
- **Focus on the happy path only**
- **If unsure whether to include something, DON'T include it**

## Out of Scope (Do Not Implement)
- Azure, GCP, vSphere, OpenStack providers
- Multiple regions beyond frm-poc
- Additional clusters beyond aws-cluster-01
- Static credential fallbacks
- Advanced pipeline features (triggers, webhooks, etc.)

## Notes
- Focus on working, minimal implementation
- Use realistic AWS resource configurations
- Include proper RBAC for pipeline execution
- Ensure all YAML is valid and follows best practices
- Add basic documentation in README.md
