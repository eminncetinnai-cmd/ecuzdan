"""Exceptions for transaction and financial ledger domains."""


class LedgerError(ValueError):
    """Defter işlemi doğrulama hatası."""


class OptimisticConcurrencyError(LedgerError):
    """İşlem güncellemesinde beklenen sürüm artık geçerli değil."""

    error_code = "CONCURRENCY_CONFLICT"
