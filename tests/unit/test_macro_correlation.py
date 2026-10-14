"""Unit tests for MacroCorrelationService."""

import pytest

from domain.ratios.data.historical_ratios_data import get_all_ratio_definitions
from domain.ratios.services.macro_correlation_service import (
    CorrelationMatrix,
    MacroCorrelationService,
)


@pytest.fixture
def service():
    return MacroCorrelationService()


def test_calculate_correlation_perfect_positive(service):
    """Test that two identical upward trends produce r = 1.00."""
    series_a = [10.0, 20.0, 30.0, 40.0, 50.0]
    series_b = [2.0, 4.0, 6.0, 8.0, 10.0]
    r = service.calculate_correlation(series_a, series_b)
    assert r == 1.00


def test_calculate_correlation_perfect_negative(service):
    """Test that two perfectly opposing series produce r = -1.00."""
    series_a = [10.0, 20.0, 30.0, 40.0, 50.0]
    series_b = [50.0, 40.0, 30.0, 20.0, 10.0]
    r = service.calculate_correlation(series_a, series_b)
    assert r == -1.00


def test_calculate_correlation_edge_cases(service):
    """Test series with fewer than 3 elements or zero variance."""
    assert service.calculate_correlation([1.0, 2.0], [3.0, 4.0]) == 0.0
    # Zero variance (constant series)
    assert service.calculate_correlation([5.0, 5.0, 5.0, 5.0], [1.0, 2.0, 3.0, 4.0]) == 0.0


def test_build_matrix_structure_and_symmetry(service):
    """Test that matrix is symmetric and diagonal is 1.00."""
    ratios = get_all_ratio_definitions()
    result = service.build_matrix(ratios)

    assert isinstance(result, CorrelationMatrix)
    assert len(result.labels) == len(service.CORE_BENCHMARK_CODES)
    assert len(result.matrix) == len(service.CORE_BENCHMARK_CODES)
    assert result.period_count >= 24

    n = len(result.labels)
    for i in range(n):
        # Diagonal must be 1.00
        assert result.matrix[i][i].coefficient == 1.00
        assert result.matrix[i][i].row_code == result.matrix[i][i].col_code

        for j in range(n):
            cell_ij = result.matrix[i][j]
            cell_ji = result.matrix[j][i]
            # Matrix must be symmetric
            assert cell_ij.coefficient == cell_ji.coefficient
            assert -1.0 <= cell_ij.coefficient <= 1.0
            assert cell_ij.strength_label != ""
            assert cell_ij.color_class.startswith("corr-")
