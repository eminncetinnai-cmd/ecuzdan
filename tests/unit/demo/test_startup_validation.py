"""Unit tests for DemoDataStartupValidator."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from tempfile import TemporaryDirectory
import os

from domain.demo.startup_validation import DemoDataStartupValidator, validate_demo_data_config


class TestDemoDataStartupValidator:
    """Test DemoDataStartupValidator functionality."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary directory for config files."""
        with TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def startup_validator(self, temp_config_dir):
        """Create a startup validator with temporary directory."""
        return DemoDataStartupValidator(config_dir=temp_config_dir)

    @pytest.fixture
    def mock_category_service(self):
        """Mock category service."""
        service = Mock()
        service.is_valid_category.return_value = True
        return service

    @pytest.fixture
    def mock_validator(self, mock_category_service):
        """Mock validator."""
        from domain.demo.validators.demo_data_validator import DemoDataValidator, ValidationResult
        
        validator = Mock(spec=DemoDataValidator)
        validator.category_service = mock_category_service
        
        # Mock validation results
        validator.validate_category_mappings.return_value = ValidationResult(
            is_valid=True, errors=[], warnings=[]
        )
        validator.validate_generation_rules.return_value = ValidationResult(
            is_valid=True, errors=[], warnings=[]
        )
        validator.validate_data_templates.return_value = ValidationResult(
            is_valid=True, errors=[], warnings=[]
        )
        
        return validator

    def test_validate_all_success(self, startup_validator, temp_config_dir, mock_validator):
        """Test successful validation of all configurations."""
        # Create minimal valid config files
        category_mappings = {
            'income': {'salary': {'standard_name': 'Maaş', 'category_type': 'Gelir'}}
        }
        generation_rules = {
            'income_rules': {
                'salary': {
                    'base_amount': 50000,
                    'amount_range': {'min': 45000, 'max': 55000}
                }
            }
        }
        data_templates = {
            'transaction_templates': {
                'monthly_salary': {
                    'category_mapping': 'salary',
                    'description_template': 'Test',
                    'amount_rule': 'salary',
                    'type': 'Gelir'
                }
            }
        }
        
        import yaml
        with open(os.path.join(temp_config_dir, 'category_mappings.yaml'), 'w') as f:
            yaml.dump(category_mappings, f)
        with open(os.path.join(temp_config_dir, 'generation_rules.yaml'), 'w') as f:
            yaml.dump(generation_rules, f)
        with open(os.path.join(temp_config_dir, 'data_templates.yaml'), 'w') as f:
            yaml.dump(data_templates, f)
        
        # Patch validator
        startup_validator.validator = mock_validator
        
        result = startup_validator.validate_all()
        
        assert result is True

    def test_validate_all_with_warnings(self, startup_validator, temp_config_dir, mock_validator):
        """Test validation with warnings."""
        # Create config with warning (status distribution not summing to 1.0)
        category_mappings = {
            'income': {'salary': {'standard_name': 'Maaş', 'category_type': 'Gelir'}}
        }
        generation_rules = {
            'income_rules': {
                'salary': {
                    'base_amount': 50000,
                    'amount_range': {'min': 45000, 'max': 55000},
                    'status_distribution': {'Ödendi': 0.8, 'Gecikti': 0.3}  # Sum = 1.1
                }
            }
        }
        data_templates = {
            'transaction_templates': {
                'monthly_salary': {
                    'category_mapping': 'salary',
                    'description_template': 'Test',
                    'amount_rule': 'salary',
                    'type': 'Gelir'
                }
            }
        }
        
        import yaml
        with open(os.path.join(temp_config_dir, 'category_mappings.yaml'), 'w') as f:
            yaml.dump(category_mappings, f)
        with open(os.path.join(temp_config_dir, 'generation_rules.yaml'), 'w') as f:
            yaml.dump(generation_rules, f)
        with open(os.path.join(temp_config_dir, 'data_templates.yaml'), 'w') as f:
            yaml.dump(data_templates, f)
        
        # Mock validator with warning
        from domain.demo.validators.demo_data_validator import ValidationResult
        mock_validator.validate_generation_rules.return_value = ValidationResult(
            is_valid=True, errors=[], warnings=['Status distribution does not sum to 1.0']
        )
        startup_validator.validator = mock_validator
        
        result = startup_validator.validate_all()
        
        # Should still pass (warnings don't fail validation)
        assert result is True

    def test_validate_all_with_errors(self, startup_validator, temp_config_dir, mock_validator):
        """Test validation with errors."""
        # Create config with error (missing required field)
        category_mappings = {
            'income': {'salary': {'standard_name': 'Maaş', 'category_type': 'Gelir'}}
        }
        generation_rules = {
            'income_rules': {
                'salary': {
                    'base_amount': 50000,
                    # Missing amount_range
                }
            }
        }
        data_templates = {
            'transaction_templates': {
                'monthly_salary': {
                    'category_mapping': 'salary',
                    'description_template': 'Test',
                    'amount_rule': 'salary',
                    'type': 'Gelir'
                }
            }
        }
        
        import yaml
        with open(os.path.join(temp_config_dir, 'category_mappings.yaml'), 'w') as f:
            yaml.dump(category_mappings, f)
        with open(os.path.join(temp_config_dir, 'generation_rules.yaml'), 'w') as f:
            yaml.dump(generation_rules, f)
        with open(os.path.join(temp_config_dir, 'data_templates.yaml'), 'w') as f:
            yaml.dump(data_templates, f)
        
        # Mock validator with error
        from domain.demo.validators.demo_data_validator import ValidationResult
        mock_validator.validate_generation_rules.return_value = ValidationResult(
            is_valid=False, errors=['Missing required field: amount_range'], warnings=[]
        )
        startup_validator.validator = mock_validator
        
        result = startup_validator.validate_all()
        
        # Should fail due to missing required field
        assert result is False

    def test_validate_with_tenant(self, startup_validator, temp_config_dir, mock_validator):
        """Test validation with tenant context."""
        # Create minimal valid config files
        category_mappings = {
            'income': {'salary': {'standard_name': 'Maaş', 'category_type': 'Gelir'}}
        }
        generation_rules = {
            'income_rules': {
                'salary': {
                    'base_amount': 50000,
                    'amount_range': {'min': 45000, 'max': 55000}
                }
            }
        }
        data_templates = {
            'transaction_templates': {
                'monthly_salary': {
                    'category_mapping': 'salary',
                    'description_template': 'Test',
                    'amount_rule': 'salary',
                    'type': 'Gelir'
                }
            }
        }
        
        import yaml
        with open(os.path.join(temp_config_dir, 'category_mappings.yaml'), 'w') as f:
            yaml.dump(category_mappings, f)
        with open(os.path.join(temp_config_dir, 'generation_rules.yaml'), 'w') as f:
            yaml.dump(generation_rules, f)
        with open(os.path.join(temp_config_dir, 'data_templates.yaml'), 'w') as f:
            yaml.dump(data_templates, f)
        
        # Directly set the validator to our mock
        startup_validator.validator = mock_validator
        result = startup_validator.validate_with_tenant('test-tenant')
        
        assert result is True

    def test_validate_demo_data_config_convenience(self, temp_config_dir):
        """Test convenience function for validation."""
        # Create minimal valid config files
        category_mappings = {
            'income': {'salary': {'standard_name': 'Maaş', 'category_type': 'Gelir'}}
        }
        generation_rules = {
            'income_rules': {
                'salary': {
                    'base_amount': 50000,
                    'amount_range': {'min': 45000, 'max': 55000}
                }
            }
        }
        data_templates = {
            'transaction_templates': {
                'monthly_salary': {
                    'category_mapping': 'salary',
                    'description_template': 'Test',
                    'amount_rule': 'salary',
                    'type': 'Gelir'
                }
            }
        }
        
        import yaml
        with open(os.path.join(temp_config_dir, 'category_mappings.yaml'), 'w') as f:
            yaml.dump(category_mappings, f)
        with open(os.path.join(temp_config_dir, 'generation_rules.yaml'), 'w') as f:
            yaml.dump(generation_rules, f)
        with open(os.path.join(temp_config_dir, 'data_templates.yaml'), 'w') as f:
            yaml.dump(data_templates, f)
        
        # Patch the validator
        with patch('domain.demo.startup_validation.DemoDataStartupValidator') as MockValidator:
            mock_instance = Mock()
            mock_instance.validate_all.return_value = True
            MockValidator.return_value = mock_instance
            
            result = validate_demo_data_config(config_dir=temp_config_dir)
            
            assert result is True
