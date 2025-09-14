#!/usr/bin/env python3

import unittest
import tempfile
import yaml
import os
from pathlib import Path
from generate_configs import (
    merge_nested_dicts, load_config, create_output_dirs,
    generate_configmap, generate_values_file, merge_cluster_config, generate_all, 
    find_by_name, validate_cluster_uniqueness
)
import sys

class TestConfigGenerator(unittest.TestCase):
    """Test cases for the ConfigGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_values = {
            'defaults': {
                'tasks': {
                    'test-task': 'default-value'
                },
                'data': {
                    'DEFAULT_VAR': 'default',
                    'OVERRIDABLE': 'from-default'
                }
            },
            'sectors': [
                {
                    'name': 'test-sector',
                    'tasks': {
                        'sector-task': 'sector-value'
                    },
                    'data': {
                        'SECTOR_VAR': 'sector',
                        'OVERRIDABLE': 'from-sector'
                    }
                }
            ],
            'regions': [
                {
                    'name': 'test-region',
                    'sector': 'test-sector',
                    'tasks': {
                        'region-task': 'region-value'
                    },
                    'data': {
                        'REGION_VAR': 'region',
                        'OVERRIDABLE': 'from-region'
                    }
                }
            ],
            'clusters': [
                {
                    'name': 'test-cluster',
                    'region': 'test-region',
                    'tasks': {
                        'cluster-task': 'cluster-value'
                    },
                    'data': {
                        'CLUSTER_VAR': 'cluster',
                        'OVERRIDABLE': 'from-cluster'
                    }
                }
            ]
        }
        
        # Create test values file
        self.values_file = os.path.join(self.temp_dir, 'test_values.yaml')
        with open(self.values_file, 'w') as f:
            yaml.dump(self.test_values, f)
        
        self.output_dir = os.path.join(self.temp_dir, 'output')
    
    def test_merge_nested_dicts(self):
        """Test the merge_nested_dicts function."""
        dict1 = {'a': 1, 'b': {'x': 10, 'y': 20}}
        dict2 = {'b': {'y': 30, 'z': 40}, 'c': 3}
        
        result = merge_nested_dicts(dict1, dict2)
        
        expected = {'a': 1, 'b': {'x': 10, 'y': 30, 'z': 40}, 'c': 3}
        self.assertEqual(result, expected)
    
    def test_inheritance_hierarchy(self):
        """Test that inheritance works correctly: defaults -> sector -> region -> cluster."""
        data = self.test_values
        cluster_config = data['clusters'][0]  # First cluster in the list
        cluster_name = cluster_config['name']
        
        merged = merge_cluster_config(cluster_name, cluster_config, data)
        
        # Test that all levels contribute values
        self.assertEqual(merged['data']['DEFAULT_VAR'], 'default')
        self.assertEqual(merged['data']['SECTOR_VAR'], 'sector')
        self.assertEqual(merged['data']['REGION_VAR'], 'region')
        self.assertEqual(merged['data']['CLUSTER_VAR'], 'cluster')
        
        # Test that later values override earlier ones
        self.assertEqual(merged['data']['OVERRIDABLE'], 'from-cluster')
        
        # Test that all task levels are present
        self.assertEqual(merged['tasks']['test-task'], 'default-value')
        self.assertEqual(merged['tasks']['sector-task'], 'sector-value')
        self.assertEqual(merged['tasks']['region-task'], 'region-value')
        self.assertEqual(merged['tasks']['cluster-task'], 'cluster-value')
        
        # Test that metadata is included
        self.assertEqual(merged['cluster_name'], 'test-cluster')
        self.assertEqual(merged['region'], 'test-region')
        self.assertEqual(merged['sector'], 'test-sector')
    
    def test_complex_inheritance(self):
        """Test inheritance with more complex nested structures."""
        complex_values = {
            'defaults': {
                'data': {
                    'nested': {
                        'level1': {
                            'default_key': 'default_value',
                            'override_me': 'default'
                        }
                    }
                }
            },
            'sectors': [
                {
                    'name': 'complex-sector',
                    'data': {
                        'nested': {
                            'level1': {
                                'sector_key': 'sector_value',
                                'override_me': 'sector'
                            }
                        }
                    }
                }
            ],
            'regions': [
                {
                    'name': 'complex-region',
                    'sector': 'complex-sector',
                    'data': {
                        'nested': {
                            'level1': {
                                'region_key': 'region_value',
                                'override_me': 'region'
                            }
                        }
                    }
                }
            ],
            'clusters': [
                {
                    'name': 'complex-cluster',
                    'region': 'complex-region',
                    'data': {
                        'nested': {
                            'level1': {
                                'cluster_key': 'cluster_value',
                                'override_me': 'cluster'
                            }
                        }
                    }
                }
            ]
        }
        
        # Write temporary complex values file
        complex_values_file = os.path.join(self.temp_dir, 'complex_values.yaml')
        with open(complex_values_file, 'w') as f:
            yaml.dump(complex_values, f)
        
        cluster_config = complex_values['clusters'][0]  # First cluster in the list
        cluster_name = cluster_config['name']
        merged = merge_cluster_config(cluster_name, cluster_config, complex_values)
        
        nested_data = merged['data']['nested']['level1']
        
        # All levels should contribute their keys
        self.assertEqual(nested_data['default_key'], 'default_value')
        self.assertEqual(nested_data['sector_key'], 'sector_value')
        self.assertEqual(nested_data['region_key'], 'region_value')
        self.assertEqual(nested_data['cluster_key'], 'cluster_value')
        
        # Override should come from cluster level
        self.assertEqual(nested_data['override_me'], 'cluster')
    
    def test_find_by_name(self):
        """Test the find_by_name helper function."""
        items = [
            {'name': 'first', 'value': 1},
            {'name': 'second', 'value': 2}
        ]
        
        result = find_by_name(items, 'second')
        self.assertEqual(result, {'name': 'second', 'value': 2})
        
        with self.assertRaises(ValueError):
            find_by_name(items, 'nonexistent')
    
    def test_generate_configmap(self):
        """Test configmap generation."""
        configmaps_dir, values_dir = create_output_dirs(self.output_dir)
        
        merged_config = {
            'data': {
                'VAR1': 'value1',
                'VAR2': 'value2'
            },
            'tasks': {
                'task1': 'task-value'
            },
            'region': 'test-region',
            'sector': 'test-sector'
        }
        
        generate_configmap('test-cluster', merged_config, configmaps_dir)
        
        configmap_file = configmaps_dir / 'test-region-test-cluster-configmap.yaml'
        self.assertTrue(configmap_file.exists())
        
        with open(configmap_file, 'r') as f:
            configmap = yaml.safe_load(f)
        
        self.assertEqual(configmap['apiVersion'], 'v1')
        self.assertEqual(configmap['kind'], 'ConfigMap')
        self.assertEqual(configmap['metadata']['name'], 'test-region-test-cluster-config')
        
        # Data section should include original data plus metadata
        self.assertIn('VAR1', configmap['data'])
        self.assertIn('VAR2', configmap['data'])
        self.assertIn('REGION', configmap['data'])
        self.assertIn('SECTOR', configmap['data'])
        self.assertIn('CLUSTER_NAME', configmap['data'])
        self.assertEqual(configmap['data']['REGION'], 'test-region')
        self.assertEqual(configmap['data']['SECTOR'], 'test-sector')
        self.assertEqual(configmap['data']['CLUSTER_NAME'], 'test-cluster')
        self.assertNotIn('tasks', configmap)
    
    def test_generate_values_file(self):
        """Test values file generation."""
        configmaps_dir, values_dir = create_output_dirs(self.output_dir)
        
        merged_config = {
            'data': {
                'VAR1': 'value1'
            },
            'tasks': {
                'task1': 'task-value'
            },
            'region': 'test-region'
        }
        
        generate_values_file('test-cluster', merged_config, values_dir)
        
        values_file = values_dir / 'test-region-test-cluster-values.yaml'
        self.assertTrue(values_file.exists())
        
        with open(values_file, 'r') as f:
            values = yaml.safe_load(f)
        
        # All sections should be in values file
        self.assertIn('data', values)
        self.assertIn('tasks', values)
        self.assertEqual(values['data']['VAR1'], 'value1')
        self.assertEqual(values['tasks']['task1'], 'task-value')
    
    def test_real_world_scenario(self):
        """Test with a scenario similar to the actual values.yaml."""
        # Use the actual test values that simulate the real scenario
        data = self.test_values
        
        # Test inheritance order with OVERRIDABLE variable
        cluster_config = data['clusters'][0]  # First cluster in the list
        cluster_name = cluster_config['name']
        merged = merge_cluster_config(cluster_name, cluster_config, data)
        
        # The cluster value should win (defaults -> sector -> region -> cluster)
        self.assertEqual(merged['data']['OVERRIDABLE'], 'from-cluster')
        
        # All unique values should be present
        expected_keys = {'DEFAULT_VAR', 'SECTOR_VAR', 'REGION_VAR', 'CLUSTER_VAR', 'OVERRIDABLE'}
        actual_keys = set(merged['data'].keys())
        self.assertEqual(actual_keys, expected_keys)
        
        # Metadata should be present
        self.assertEqual(merged['cluster_name'], 'test-cluster')
        self.assertEqual(merged['region'], 'test-region')
        self.assertEqual(merged['sector'], 'test-sector')
    
    def test_cluster_uniqueness_validation_passes(self):
        """Test that valid cluster configurations pass uniqueness validation."""
        valid_clusters = [
            {'name': 'web-01', 'region': 'us-east-1'},
            {'name': 'web-02', 'region': 'us-east-1'},
            {'name': 'web-01', 'region': 'us-west-2'},  # Same name, different region - OK
            {'name': 'api-01', 'region': 'us-west-2'},
        ]
        
        # Should not raise an exception
        validate_cluster_uniqueness(valid_clusters)
    
    def test_cluster_uniqueness_validation_fails(self):
        """Test that duplicate cluster names in same region fail validation."""
        invalid_clusters = [
            {'name': 'web-01', 'region': 'us-east-1'},
            {'name': 'api-01', 'region': 'us-east-1'},
            {'name': 'web-01', 'region': 'us-east-1'},  # Duplicate name in same region
        ]
        
        with self.assertRaises(ValueError) as cm:
            validate_cluster_uniqueness(invalid_clusters)
        
        error_message = str(cm.exception)
        self.assertIn("Duplicate cluster name 'web-01' found in region 'us-east-1'", error_message)
        self.assertIn("Cluster names must be unique within each region", error_message)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)


if __name__ == '__main__':
    # Handle optional output directory argument for testing
    if len(sys.argv) > 1:
        # Remove the output directory argument so unittest doesn't see it
        sys.argv.pop(1)
    unittest.main()