# Test Documentation

## Test Architecture

The test suite is organized into a professional, maintainable structure with clear separation of concerns:

```
tests/
├── __init__.py
├── conftest.py                 # Global fixtures and test configuration
├── unit/                       # Unit tests for isolated components
│   ├── __init__.py
│   ├── test_logging_systems.py # Logging utilities tests
│   ├── test_routes_utils.py    # Route utilities tests
│   ├── test_models.py          # Model tests
│   └── financial/             # Financial domain unit tests
│       └── test_financial_ledger.py
├── integration/                # Integration tests for component interactions
│   ├── __init__.py
│   ├── test_monitoring.py     # Monitoring API integration tests
│   ├── test_admin_users.py    # Admin user management tests
│   ├── test_ai_insights.py     # AI insights integration tests
│   └── test_architecture.py    # Architecture validation tests
├── regression/                 # Regression tests for bug fix validation
│   ├── __init__.py
│   ├── test_analysis_engine_regression.py
│   ├── test_balance_invariant.py
│   ├── test_faz26_category_tenant.py
│   ├── test_financial_engine_regression.py
│   ├── test_investment_performance_regression.py
│   ├── test_simulation_runner_regression.py
│   └── test_strategy_engine_regression.py
└── e2e/                        # End-to-end tests for full system validation
    └── __init__.py
```

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/ -m unit

# Integration tests only
pytest tests/integration/ -m integration

# Regression tests only
pytest tests/regression/ -m regression

# E2E tests only
pytest tests/e2e/ -m e2e
```

### Run Specific Test Files
```bash
pytest tests/unit/test_logging_systems.py
pytest tests/integration/test_monitoring.py
```

### Run with Coverage
```bash
pytest tests/ --cov=.
pytest tests/ --cov=. --cov-report=html
```

### Run with Verbose Output
```bash
pytest tests/ -v
```

## Test Markers

Tests are categorized using pytest markers:

- `@pytest.mark.unit` - Unit tests for isolated components
- `@pytest.mark.integration` - Integration tests for component interactions
- `@pytest.mark.regression` - Regression tests for bug fix validation
- `@pytest.mark.e2e` - End-to-end tests for full system validation
- `@pytest.mark.financial` - Financial domain specific tests
- `@pytest.mark.slow` - Slow-running tests (e.g., external API calls)

## Coverage Requirements

- **Minimum Coverage**: 25% (configured in `pytest.ini`)
- **Current Coverage**: 54.45%
- **Target Coverage**: 70%+ (recommended for production)

Coverage reports are generated in `htmlcov/` directory when running with `--cov-report=html`.

## Fixtures

Global fixtures are defined in `tests/conftest.py`:

- `app` - Flask application with test configuration
- `client` - Flask test client
- `test_user` - Regular test user fixture
- `admin_user` - Admin test user fixture
- `test_category` - Test category fixture
- `test_transaction` - Test transaction fixture
- `authenticated_client` - Client with regular user authentication
- `authenticated_admin_client` - Client with admin authentication
- `container` - Dependency injection container for testing

## Test Configuration

Test configuration is defined in `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
    --cov=.
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=25

markers =
    unit: Unit tests for isolated components
    integration: Integration tests for component interactions
    regression: Regression tests for bug fix validation
    e2e: End-to-end tests for full system validation
    financial: Financial domain specific tests
    slow: Slow-running tests
```

## Writing Tests

### Unit Test Example
```python
import pytest

@pytest.mark.unit
def test_format_money():
    """Test money formatting"""
    from utils.format_utils import format_money
    
    result = format_money(1000.50)
    assert '1000.50' in result or '1.000,50' in result
```

### Integration Test Example
```python
import pytest

@pytest.mark.integration
def test_monitoring_dashboard_route(authenticated_client):
    """Test monitoring dashboard route"""
    response = authenticated_client.get('/monitoring')
    assert response.status_code == 200
    assert b'monitoring' in response.data.lower()
```

### Regression Test Example
```python
import pytest

@pytest.mark.regression
def test_turkey_macro_constants():
    """Test Turkey macro constants reflect 2026 realities"""
    from engines.analysis_engine import TURKEY_MACRO
    
    assert TURKEY_MACRO["policy_rate"] == 0.50
    assert TURKEY_MACRO["inflation"] == 0.45
```

## Best Practices

1. **Use Descriptive Test Names**: Test names should clearly describe what is being tested
2. **Follow AAA Pattern**: Arrange, Act, Assert structure in tests
3. **Use Fixtures**: Reuse fixtures for common test setup
4. **Mock External Dependencies**: Use mocks for external services (SMTP, APIs)
5. **Test Edge Cases**: Include tests for boundary conditions and error cases
6. **Keep Tests Independent**: Each test should be able to run independently
7. **Use Appropriate Markers**: Mark tests with the correct category
8. **Maintain Coverage**: Ensure new code has corresponding tests

## Test Statistics

- **Total Tests**: 1959
- **Passing**: 1959
- **Failing**: 0
- **Skipped**: 165
- **XFailed**: 1
- **Coverage**: 54.45%
- **Test Duration**: ~6 minutes

## Troubleshooting

### Tests Fail with Import Errors
- Ensure all dependencies are installed: `pip install -r configuration/dependencies/requirements.txt`
- Check that the Python path includes the project root

### Tests Fail with Database Errors
- Ensure the test database is properly configured in `conftest.py`
- Check that database migrations are up to date

### Coverage is Below Threshold
- Run tests with `--cov-report=html` to see detailed coverage report
- Identify untested code and add corresponding tests

### Tests are Slow
- Use `@pytest.mark.slow` for slow tests
- Run only fast tests: `pytest tests/ -m "not slow"`

## CI/CD Integration

For CI/CD integration, add the following to your pipeline:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: pytest tests/ --cov=. --cov-fail-under=25

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-Cov Documentation](https://pytest-cov.readthedocs.io/)
- [Flask Testing Documentation](https://flask.palletsprojects.com/en/latest/testing/)
