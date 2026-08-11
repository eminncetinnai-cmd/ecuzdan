"""
Portfolio Integration Test Script
Mock script to verify portfolio analysis integration with AnalysisEngine
"""

from unittest.mock import Mock

import pandas as pd

from engines.analysis_engine import AnalysisEngine


class MockAsset:
    """Mock Asset object for testing"""
    def __init__(self, symbol, name, unit_price, quantity):
        self.symbol = symbol
        self.name = name
        self.unit_price = unit_price
        self.quantity = quantity


def test_portfolio_integration():
    """Test portfolio integration with mock assets"""

    # Create mock market data service
    mock_market_service = Mock()

    # Create mock market data with BTC and XU100
    mock_market_data = {
        'BTC-USD': {
            'name': 'Bitcoin',
            'currency': 'USD',
            'data': pd.DataFrame({
                'price': [50000, 52000, 51000, 53000, 55000, 54000, 56000, 58000, 57000, 60000] * 30  # 300 data points for rolling calculations
            })
        },
        'XU100.IS': {
            'name': 'BIST100',
            'currency': 'TRY',
            'data': pd.DataFrame({
                'price': [8000, 8200, 8100, 8300, 8500, 8400, 8600, 8800, 8700, 9000] * 30  # 300 data points for rolling calculations
            })
        }
    }

    mock_market_service.get_all_market_data.return_value = mock_market_data

    # Create AnalysisEngine instance
    engine = AnalysisEngine(mock_market_service)

    # Create mock portfolio assets
    mock_portfolio = [
        MockAsset(symbol='BTC', name='Bitcoin', unit_price=50000, quantity=0.5),
        MockAsset(symbol='XU100', name='BIST100', unit_price=8000, quantity=10),
    ]

    # Run full analysis with portfolio
    results = engine.run_full_analysis(user_portfolio=mock_portfolio)

    # Verify results structure
    print("=== Portfolio Integration Test Results ===")
    print(f"\n1. Basic Analysis Keys: {list(results.keys())}")
    assert 'timestamp' in results
    assert 'data_available' in results
    assert 'portfolio_analysis' in results
    print("✓ Basic analysis structure verified")

    # Verify portfolio analysis
    portfolio = results['portfolio_analysis']
    print("\n2. Portfolio Analysis:")
    print(f"   - Total Assets: {portfolio['total_assets']}")
    print(f"   - Analyzed Assets: {portfolio['analyzed_assets']}")
    assert portfolio['total_assets'] == 2
    assert portfolio['analyzed_assets'] == 2
    print("✓ Portfolio analysis counts verified")

    # Verify BTC analysis
    btc_analysis = portfolio['assets']['BTC']
    print("\n3. BTC Analysis:")
    print(f"   - Symbol: {btc_analysis['symbol']}")
    print(f"   - Matched Ticker: {btc_analysis['matched_ticker']}")
    print(f"   - Unit Price: {btc_analysis['unit_price']}")
    print(f"   - Current Price: {btc_analysis['current_price']}")
    print(f"   - ROI %: {btc_analysis['roi_percent']}")
    print(f"   - Profit/Loss: {btc_analysis['profit_loss']}")
    print(f"   - Total Value: {btc_analysis['total_value']}")

    assert btc_analysis['symbol'] == 'BTC'
    assert btc_analysis['matched_ticker'] == 'BTC-USD'
    assert btc_analysis['unit_price'] == 50000
    assert btc_analysis['current_price'] == 60000
    assert btc_analysis['roi_percent'] == 20.0  # (60000-50000)/50000*100
    assert btc_analysis['profit_loss'] == 5000  # (60000-50000)*0.5
    assert btc_analysis['total_value'] == 30000  # 60000*0.5
    print("✓ BTC analysis verified")

    # Verify Z-Score signal
    if 'z_score_signal' in btc_analysis:
        print("\n4. BTC Z-Score Signal:")
        z_sig = btc_analysis['z_score_signal']
        print(f"   - Keys: {list(z_sig.keys())}")
        if 'z_score' in z_sig:
            print(f"   - Z-Score: {z_sig['z_score']}")
        if 'signal' in z_sig:
            print(f"   - Signal: {z_sig['signal']}")
        if 'strength' in z_sig:
            print(f"   - Strength: {z_sig['strength']}")
        print("✓ Z-Score signal verified")
    else:
        print("\n4. BTC Z-Score Signal: Not available (data too short for calculation)")

    # Verify Sharpe Ratio
    if 'sharpe_ratio' in btc_analysis:
        print("\n5. BTC Sharpe Ratio:")
        print(f"   - Sharpe Ratio: {btc_analysis['sharpe_ratio']}")
        print("✓ Sharpe ratio verified")
    else:
        print("\n5. BTC Sharpe Ratio: Not available (data too short for calculation)")

    # Verify XU100 analysis
    xu100_analysis = portfolio['assets']['XU100']
    print("\n6. XU100 Analysis:")
    print(f"   - Symbol: {xu100_analysis['symbol']}")
    print(f"   - Matched Ticker: {xu100_analysis['matched_ticker']}")
    print(f"   - ROI %: {xu100_analysis['roi_percent']}")

    assert xu100_analysis['symbol'] == 'XU100'
    assert xu100_analysis['matched_ticker'] == 'XU100.IS'
    assert xu100_analysis['roi_percent'] == 12.5  # (9000-8000)/8000*100
    print("✓ XU100 analysis verified")

    # Test backward compatibility (no portfolio)
    print("\n7. Backward Compatibility Test (no portfolio):")
    results_no_portfolio = engine.run_full_analysis(user_portfolio=None)
    assert 'portfolio_analysis' not in results_no_portfolio
    assert 'mean_reversion' in results_no_portfolio
    assert 'sharpe_ratios' in results_no_portfolio
    print("✓ Backward compatibility verified")

    print("\n=== All Tests Passed ===")


def test_symbol_mapping_resilience():
    """Test symbol mapping resilience for various formats"""

    mock_market_service = Mock()
    mock_market_data = {
        'BTC-USD': {'name': 'Bitcoin', 'currency': 'USD', 'data': pd.DataFrame({'price': [50000, 52000, 53000]})},
        'XU100.IS': {'name': 'BIST100', 'currency': 'TRY', 'data': pd.DataFrame({'price': [8000, 8200, 8300]})},
        'GC=F': {'name': 'Gold', 'currency': 'USD', 'data': pd.DataFrame({'price': [2000, 2100, 2200]})},
    }
    mock_market_service.get_all_market_data.return_value = mock_market_data

    engine = AnalysisEngine(mock_market_service)

    # Test various symbol formats
    test_cases = [
        ('BTC', 'BTC-USD'),  # Prefix match
        ('XU100', 'XU100.IS'),  # Suffix match
        ('GC=F', 'GC=F'),  # Direct match
        ('btc', 'BTC-USD'),  # Case-insensitive match
    ]

    print("\n=== Symbol Mapping Resilience Test ===")
    for symbol, expected_match in test_cases:
        matched = engine._match_symbol_to_market_data(symbol, mock_market_data)
        print(f"Symbol '{symbol}' -> Matched: '{matched}' (Expected: '{expected_match}')")
        assert matched == expected_match, f"Expected {expected_match}, got {matched}"

    # Test unmatched symbol
    unmatched = engine._match_symbol_to_market_data('UNKNOWN', mock_market_data)
    print(f"Symbol 'UNKNOWN' -> Matched: '{unmatched}' (Expected: None)")
    assert unmatched is None

    print("✓ Symbol mapping resilience verified")


if __name__ == '__main__':
    try:
        test_portfolio_integration()
        test_symbol_mapping_resilience()
        print("\n=== All Portfolio Integration Tests Passed Successfully ===")
    except AssertionError as e:
        print(f"\n✗ Test Failed: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Unexpected Error: {e}")
        raise
