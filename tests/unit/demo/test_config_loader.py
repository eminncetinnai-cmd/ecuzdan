"""Unit tests for DemoDataConfigLoader."""

import os
import tempfile

import pytest
import yaml

from domain.demo.config_loader import DemoDataConfigLoader


class TestDemoDataConfigLoader:
    """Test DemoDataConfigLoader functionality."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary directory for config files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def config_loader(self, temp_config_dir):
        """Create a config loader with temporary directory."""
        return DemoDataConfigLoader(config_dir=temp_config_dir)

    @pytest.fixture
    def sample_category_mappings(self):
        """Sample category mappings data."""
        return {
            'income': {
                'salary': {
                    'standard_name': 'Maaş / Ücret Geliri',
                    'description': 'Monthly salary income',
                    'category_type': 'Gelir'
                }
            },
            'expense': {
                'food': {
                    'standard_name': 'Market & Gıda',
                    'description': 'Food expenses',
                    'category_type': 'Gider'
                }
            }
        }

    @pytest.fixture
    def sample_generation_rules(self):
        """Sample generation rules data."""
        return {
            'income_rules': {
                'salary': {
                    'base_amount': 50000,
                    'amount_range': {'min': 45000, 'max': 55000},
                    'variation_percent': 0.10,
                    'frequency': 'monthly',
                    'payment_day': 15,
                    'status_distribution': {'Ödendi': 0.90, 'Gecikti': 0.10}
                }
            },
            'global_settings': {
                'inflation_rate': 0.40,
                'salary_growth_rate': 0.08
            }
        }

    @pytest.fixture
    def sample_data_templates(self):
        """Sample data templates data."""
        return {
            'transaction_templates': {
                'monthly_salary': {
                    'name': 'Aylık Maaş {year}',
                    'category_mapping': 'salary',
                    'description_template': '{year}-{month} maaş ödemesi',
                    'amount_rule': 'salary',
                    'frequency': 'monthly',
                    'day': 15,
                    'type': 'Gelir'
                }
            },
            'recurring_plan_templates': {
                'salary_plan': {
                    'name': 'Maaş Planı',
                    'category_mapping': 'salary',
                    'amount_rule': 'salary',
                    'installments': 12,
                    'payment_day': 1,
                    'type': 'Gelir'
                }
            }
        }

    def test_load_category_mappings(self, config_loader, temp_config_dir, sample_category_mappings):
        """Test loading category mappings from YAML."""
        filepath = os.path.join(temp_config_dir, 'category_mappings.yaml')
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(sample_category_mappings, f)

        result = config_loader.load_category_mappings()

        assert result == sample_category_mappings
        assert 'income' in result
        assert 'salary' in result['income']
        assert result['income']['salary']['standard_name'] == 'Maaş / Ücret Geliri'

    def test_load_generation_rules(self, config_loader, temp_config_dir, sample_generation_rules):
        """Test loading generation rules from YAML."""
        filepath = os.path.join(temp_config_dir, 'generation_rules.yaml')
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(sample_generation_rules, f)

        result = config_loader.load_generation_rules()

        assert result == sample_generation_rules
        assert 'income_rules' in result
        assert 'salary' in result['income_rules']
        assert result['income_rules']['salary']['base_amount'] == 50000

    def test_load_data_templates(self, config_loader, temp_config_dir, sample_data_templates):
        """Test loading data templates from YAML."""
        filepath = os.path.join(temp_config_dir, 'data_templates.yaml')
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(sample_data_templates, f)

        result = config_loader.load_data_templates()

        assert result == sample_data_templates
        assert 'transaction_templates' in result
        assert 'monthly_salary' in result['transaction_templates']

    def test_get_standard_category_name(self, config_loader, temp_config_dir, sample_category_mappings):
        """Test getting standard category name for logical name."""
        filepath = os.path.join(temp_config_dir, 'category_mappings.yaml')
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(sample_category_mappings, f)

        result = config_loader.get_standard_category_name('salary', 'income')

        assert result == 'Maaş / Ücret Geliri'

    def test_get_standard_category_name_not_found(self, config_loader, temp_config_dir, sample_category_mappings):
        """Test getting standard category name for non-existent logical name."""
        filepath = os.path.join(temp_config_dir, 'category_mappings.yaml')
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(sample_category_mappings, f)

        result = config_loader.get_standard_category_name('nonexistent', 'income')

        assert result is None

    def test_get_generation_rule(self, config_loader, temp_config_dir, sample_generation_rules):
        """Test getting generation rule by name and type."""
        filepath = os.path.join(temp_config_dir, 'generation_rules.yaml')
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(sample_generation_rules, f)

        result = config_loader.get_generation_rule('salary', 'income_rules')

        assert result is not None
        assert result['base_amount'] == 50000
        assert result['payment_day'] == 15

    def test_get_transaction_template(self, config_loader, temp_config_dir, sample_data_templates):
        """Test getting transaction template by name."""
        filepath = os.path.join(temp_config_dir, 'data_templates.yaml')
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(sample_data_templates, f)

        result = config_loader.get_transaction_template('monthly_salary')

        assert result is not None
        assert result['category_mapping'] == 'salary'
        assert result['type'] == 'Gelir'

    def test_get_recurring_plan_template(self, config_loader, temp_config_dir, sample_data_templates):
        """Test getting recurring plan template by name."""
        filepath = os.path.join(temp_config_dir, 'data_templates.yaml')
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(sample_data_templates, f)

        result = config_loader.get_recurring_plan_template('salary_plan')

        assert result is not None
        assert result['category_mapping'] == 'salary'
        assert result['installments'] == 12

    def test_get_global_settings(self, config_loader, temp_config_dir, sample_generation_rules):
        """Test getting global settings."""
        filepath = os.path.join(temp_config_dir, 'generation_rules.yaml')
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(sample_generation_rules, f)

        result = config_loader.get_global_settings()

        assert result is not None
        assert result['inflation_rate'] == 0.40
        assert result['salary_growth_rate'] == 0.08

    def test_reload_configs(self, config_loader, temp_config_dir, sample_category_mappings):
        """Test reloading configuration files."""
        filepath = os.path.join(temp_config_dir, 'category_mappings.yaml')
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(sample_category_mappings, f)

        # Load first time
        result1 = config_loader.load_category_mappings()
        assert result1 is not None

        # Modify file
        sample_category_mappings['income']['salary']['standard_name'] = 'Updated Maaş'
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(sample_category_mappings, f)

        # Reload
        config_loader.reload_configs()
        result2 = config_loader.load_category_mappings()

        assert result2['income']['salary']['standard_name'] == 'Updated Maaş'

    def test_caching(self, config_loader, temp_config_dir, sample_category_mappings):
        """Test that configurations are cached."""
        filepath = os.path.join(temp_config_dir, 'category_mappings.yaml')
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(sample_category_mappings, f)

        # Load first time
        result1 = config_loader.load_category_mappings()

        # Load second time (should use cache)
        result2 = config_loader.load_category_mappings()

        assert result1 is result2  # Same object reference (cached)
