# Regionality - GitOps CAPI Cluster Provisioning

Minimal proof of concept for AWS EKS cluster provisioning using Tekton pipelines and ArgoCD.

## Scope
- **Provider**: AWS EKS only
- **Region**: frm-poc only
- **Cluster**: aws-cluster-01
- **Authentication**: STS cross-account role assumption

## Structure
- `bootstrap/` - ArgoCD app-of-apps configuration
- `tekton/` - Pipeline definitions with regional/cluster overlays
- `clusters/` - CAPI cluster definitions
- `config/` - AWS account and role configuration

## Usage
1. Deploy ArgoCD app-of-apps: `kubectl apply -f bootstrap/argocd/app-of-apps.yaml`
2. ArgoCD will sync Tekton pipelines and cluster definitions
3. Trigger pipeline to provision EKS cluster in frm-poc region

## Adding New Regions and Clusters

### Adding a New Region (e.g., us-west-2)

1. **Create region overlay**:
   ```bash
   mkdir -p tekton/overlays/regions/us-west-2
   ```

2. **Copy and modify region configuration**:
   ```bash
   cp tekton/overlays/regions/frm-poc/kustomization.yaml tekton/overlays/regions/us-west-2/
   cp tekton/overlays/regions/frm-poc/region-config.yaml tekton/overlays/regions/us-west-2/
   ```
   Edit `us-west-2/region-config.yaml` to update role ARN and defaults.

3. **Create account configuration**:
   ```bash
   cp config/accounts/aws/frm-poc-shared.yaml config/accounts/aws/us-west-2-shared.yaml
   ```
   Update account ID and region in the new file.

4. **Create role configuration**:
   ```bash
   cp config/credentials/aws/sts-roles/frm-poc-account-role.yaml config/credentials/aws/sts-roles/us-west-2-account-role.yaml
   ```
   Update role ARN for the new region.

### Adding a New Cluster (e.g., aws-cluster-02 in existing region)

1. **Create cluster overlay**:
   ```bash
   mkdir -p tekton/overlays/clusters/frm-poc/aws-cluster-02
   ```

2. **Copy and modify cluster configuration**:
   ```bash
   cp tekton/overlays/clusters/frm-poc/aws-cluster-01/kustomization.yaml tekton/overlays/clusters/frm-poc/aws-cluster-02/
   cp tekton/overlays/clusters/frm-poc/aws-cluster-01/cluster-config.yaml tekton/overlays/clusters/frm-poc/aws-cluster-02/
   ```
   Edit `cluster-config.yaml` to update cluster name.

3. **Create cluster definition**:
   ```bash
   mkdir -p clusters/frm-poc/aws-cluster-02
   cp clusters/frm-poc/aws-cluster-01/kustomization.yaml clusters/frm-poc/aws-cluster-02/
   cp clusters/frm-poc/aws-cluster-01/cluster.yaml clusters/frm-poc/aws-cluster-02/
   ```
   Update all cluster names in `cluster.yaml`.

4. **Add ArgoCD application**:
   Create `bootstrap/argocd/applications/aws-cluster-02.yaml` pointing to the new cluster path.

### Triggering Pipeline

Run pipeline with parameters:
```bash
tkn pipeline start provision-eks-cluster \
  --param cluster-name=aws-cluster-01 \
  --param target-role-arn=arn:aws:iam::123456789012:role/frm-poc-provisioning-role \
  --param cluster-config-path=clusters/frm-poc/aws-cluster-01
```
