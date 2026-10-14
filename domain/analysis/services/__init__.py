"""Analysis domain services with on-demand lazy loading."""
import importlib

__all__ = [
    "BenchmarkComparator",
    "ComprehensiveReturnCalculator",
    "EnhancedCategorization",
    "InflationAnalyzer",
    "LogbookService",
    "CurrencyManager",
    "RiskAnalyzer",
    "TaxonomyService",
    "StrategyEngine",
    "StrategyService",
    # financial_guide_data
    "get_guide_data",
    "get_all_phases",
    "get_all_topics",
    "get_formula_function",
    "get_dictionary_term",
    "get_all_dictionary_terms",
    "PROGRAM_CALCULATIONS",
    "TECHNICAL_TERMS",
    "PROGRAM_ANALYSES",
]

_SERVICE_MAP = {
    "BenchmarkComparator": (".benchmark_comparison", "BenchmarkComparator"),
    "ComprehensiveReturnCalculator": (".comprehensive_return", "ComprehensiveReturnCalculator"),
    "EnhancedCategorization": (".enhanced_categorization", "EnhancedCategorization"),
    "InflationAnalyzer": (".inflation_analysis", "InflationAnalyzer"),
    "LogbookService": (".logbook_service", "LogbookService"),
    "CurrencyManager": (".multi_currency", "CurrencyManager"),
    "RiskAnalyzer": (".risk_analysis", "RiskAnalyzer"),
    "StrategyEngine": (".strategy_engine", "StrategyEngine"),
    "StrategyService": (".strategy_service", "StrategyService"),
    "TaxonomyService": (".taxonomy_service", "TaxonomyService"),
    "get_guide_data": (".financial_guide_data", "get_guide_data"),
    "get_all_phases": (".financial_guide_data", "get_all_phases"),
    "get_all_topics": (".financial_guide_data", "get_all_topics"),
    "get_formula_function": (".financial_guide_data", "get_formula_function"),
    "get_dictionary_term": (".financial_guide_data", "get_dictionary_term"),
    "get_all_dictionary_terms": (".financial_guide_data", "get_all_dictionary_terms"),
    "PROGRAM_CALCULATIONS": (".financial_guide_data", "PROGRAM_CALCULATIONS"),
    "TECHNICAL_TERMS": (".financial_guide_data", "TECHNICAL_TERMS"),
    "PROGRAM_ANALYSES": (".financial_guide_data", "PROGRAM_ANALYSES"),
}


def __getattr__(name: str):
    if name in _SERVICE_MAP:
        mod_rel, attr = _SERVICE_MAP[name]
        mod = importlib.import_module(mod_rel, package=__name__)
        val = getattr(mod, attr)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
