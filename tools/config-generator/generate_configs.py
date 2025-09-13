#!/usr/bin/env python3

import yaml
import sys
from pathlib import Path
from typing import Dict, Any


def merge_nested_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries recursively."""
    if not dicts:
        return {}

    result = dicts[0].copy()

    for dict_to_merge in dicts[1:]:
        for key, value in dict_to_merge.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_nested_dicts(result[key], value)
            else:
                result[key] = value

    return result


def load_config(values_file: str = "values.yaml") -> Dict[str, Any]:
    """Load the YAML configuration file."""
    with open(values_file, 'r') as f:
        return yaml.safe_load(f)


def create_output_dirs(output_dir: str):
    """Create output directories if they don't exist."""
    output_path = Path(output_dir)
    configmaps_dir = output_path / "configmaps"
    values_dir = output_path / "values"
    configmaps_dir.mkdir(parents=True, exist_ok=True)
    values_dir.mkdir(parents=True, exist_ok=True)
    return configmaps_dir, values_dir


def generate_configmap(cluster_name: str, merged_config: Dict[str, Any], configmaps_dir: Path):
    """Generate a ConfigMap YAML file for a cluster (data section only)."""
    if 'data' not in merged_config:
        return

    data = {k: str(v) for k, v in merged_config['data'].items()}
    data['REGION'] = merged_config['region']
    data['SECTOR'] = merged_config['sector']
    data['CLUSTER_NAME'] = cluster_name

    configmap = {
        'apiVersion': 'v1',
        'kind': 'ConfigMap',
        'metadata': {
            'name': f'{merged_config["region"]}-{cluster_name}-config',
            'namespace': 'default'
        },
        'data': data
    }

    output_file = configmaps_dir / (merged_config["configmap"] + ".yaml")
    with open(output_file, 'w') as f:
        yaml.dump(configmap, f, default_flow_style=False, sort_keys=True)


def generate_values_file(cluster_name: str, merged_config: Dict[str, Any], values_dir: Path):
    """Generate a values YAML file for a cluster (all sections)."""
    output_file = values_dir / f'{merged_config["region"]}-{cluster_name}-values.yaml'
    with open(output_file, 'w') as f:
        yaml.dump(merged_config, f, default_flow_style=False, sort_keys=True)


def find_by_name(items: list, name: str) -> Dict[str, Any]:
    """Find an item by name in a list of dictionaries."""
    for item in items:
        if item.get("name") == name:
            return item
    raise ValueError(f"Item with name '{name}' not found")


def merge_cluster_config(cluster_name: str, cluster_config: Dict[str, Any],
                       data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge configuration for a specific cluster following inheritance hierarchy.

    Args:
        cluster_name: Name of the cluster
        cluster_config: Cluster-specific configuration
        data: Full configuration data containing defaults, sectors, regions

    Returns:
        Merged configuration for the cluster with metadata
    """
    region_name = cluster_config["region"]
    region = find_by_name(data["regions"], region_name)
    sector_name = region["sector"]
    sector = find_by_name(data["sectors"], sector_name)
    defaults = data["defaults"]

    # Merge in inheritance order: defaults -> sector -> region -> cluster
    merged = merge_nested_dicts(defaults, sector, region, cluster_config)

    # Add metadata about cluster hierarchy
    merged["cluster_name"] = cluster_name
    merged["region"] = region_name
    merged["sector"] = sector_name
    merged["configmap"] = f"{region_name}-{cluster_name}-config"

    return merged


def validate_cluster_uniqueness(clusters: list) -> None:
    """Validate that cluster names are unique within each region."""
    region_clusters = {}

    for cluster in clusters:
        cluster_name = cluster["name"]
        region = cluster["region"]

        if region not in region_clusters:
            region_clusters[region] = set()

        if cluster_name in region_clusters[region]:
            raise ValueError(f"Duplicate cluster name '{cluster_name}' found in region '{region}'. "
                           f"Cluster names must be unique within each region.")

        region_clusters[region].add(cluster_name)

    print(f"✅ Cluster uniqueness validation passed")


def generate_all(output_dir: str, values_file: str = "../../values.yaml", ):
    """Generate all configmaps and values files for all clusters."""
    print(f"Loading configuration from {values_file}")
    data = load_config(values_file)

    configmaps_dir, values_dir = create_output_dirs(output_dir)
    print(f"Creating output directories: {configmaps_dir}, {values_dir}")

    clusters = data.get("clusters", {})
    print(f"Found {len(clusters)} clusters to process")

    # Validate cluster name uniqueness within regions
    validate_cluster_uniqueness(clusters)

    for cluster in clusters:
        cluster_name = cluster["name"]
        region = cluster["region"]
        print(f"Processing cluster: {cluster_name} in region: {region}")

        # Merge configuration following inheritance hierarchy
        merged_config = merge_cluster_config(cluster_name, cluster, data)

        # Generate configmap (data section only)
        generate_configmap(cluster_name, merged_config, configmaps_dir)

        # Generate values file (all sections)
        generate_values_file(cluster_name, merged_config, values_dir)

    print(f"Generated {len(clusters)} configmaps in {configmaps_dir}")
    print(f"Generated {len(clusters)} values files in {values_dir}")


def main():
    """Main entry point."""
    generate_all(output_dir=sys.argv[1])


if __name__ == "__main__":
    main()
