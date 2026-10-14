"""
Shared constants for the E-Cüzdan application.

Bu dosya tüm katmanlarda (domain, application, routes, engines) kullanılan
sabit değerleri merkezi olarak tanımlar. Magic string/sayı kullanımını önler.

AI Agent için: Bir sabit arıyorsan önce bu dosyaya bak.
Kaynak: shared/constants.py
"""

from decimal import Decimal
from typing import Final

# ---------------------------------------------------------------------------
# Turkish month names
# ---------------------------------------------------------------------------
MONTH_NAMES_TR: Final[list[str]] = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]

# ---------------------------------------------------------------------------
# Chart & UI Color Standards
# Kullanım: Canvas JS'de → CHART_COLORS['income']
#           Şablonda    → Tailwind class (text-emerald-500 vb.)
# UYARI: Bu hex değerleri Canvas 2D context için fallback'tir.
#        Şablonda asla hardcoded hex kullanma; Tailwind token kullan.
# ---------------------------------------------------------------------------
CHART_COLORS: Final[dict[str, str]] = {
    "income":     "#10b981",  # Emerald-500  — Gelir
    "expense":    "#ef4444",  # Rose-500     — Gider
    "investment": "#0ea5e9",  # Sky-500      — Yatırım
    "purple":     "#6366f1",  # Indigo-500   — Genel / Plan
    "amber":      "#f59e0b",  # Amber-500    — Altın / Uyarı
    "slate":      "#64748b",  # Slate-500    — Transfer / Nötr
    "orange":     "#f97316",  # Orange-500   — Borç / Kripto
}

# ---------------------------------------------------------------------------
# Ticker (Market Bar) Formatting
# Kullanım: {{ live.gold|format_ticker_price }} → "6.894,70"
# ---------------------------------------------------------------------------
TICKER_DECIMAL_PLACES: Final[dict[str, int]] = {
    "gold": 2,   # Gram altın TRY fiyatı — 2 ondalık basamak
    "usd":  2,   # USD/TRY
    "eur":  2,   # EUR/TRY
}

# ---------------------------------------------------------------------------
# Gold Conversion
# Kullanım: domain/analysis/services/fx_metals_provider.py
# ---------------------------------------------------------------------------
GOLD_GRAMS_PER_TROY_OUNCE: Final[Decimal] = Decimal("31.1034768")

# ---------------------------------------------------------------------------
# Transaction Types (DB'de saklanan değerler — değiştirme!)
# Kaynak: domain/transactions/constants.py
# Kullanım: Transaction.type alanı, UI renklendirmesi için CHART_COLORS ile eşleş
# ---------------------------------------------------------------------------
TRANSACTION_TYPE_INCOME:     Final[str] = "Gelir"
TRANSACTION_TYPE_EXPENSE:    Final[str] = "Gider"
TRANSACTION_TYPE_INVESTMENT: Final[str] = "Yatırım"
TRANSACTION_TYPE_TRANSFER:   Final[str] = "Transfer"

# ---------------------------------------------------------------------------
# Transaction Statuses
# ---------------------------------------------------------------------------
TRANSACTION_STATUS_PAID:    Final[str] = "Ödendi"
TRANSACTION_STATUS_PENDING: Final[str] = "Bekliyor"

# ---------------------------------------------------------------------------
# RecurringPlan Types
# ---------------------------------------------------------------------------
PLAN_TYPE_INSTALLMENT:  Final[str] = "Taksit"
PLAN_TYPE_SUBSCRIPTION: Final[str] = "Abonelik"
PLAN_TYPE_DCA:          Final[str] = "DCA"       # Dollar-Cost Averaging
PLAN_TYPE_RENT:         Final[str] = "Kira"

PLAN_STATUS_ACTIVE:    Final[str] = "Aktif"
PLAN_STATUS_COMPLETED: Final[str] = "Tamamlandı"
PLAN_STATUS_CANCELLED: Final[str] = "İptal"

# ---------------------------------------------------------------------------
# User Roles
# ---------------------------------------------------------------------------
ROLE_USER:             Final[str] = "kullanici"
ROLE_TENANT_ADMIN:     Final[str] = "tenant_admin"
ROLE_MANAGER:          Final[str] = "yonetici"
ROLE_SYSTEM_ADMIN:     Final[str] = "sistem_yoneticisi"

# ---------------------------------------------------------------------------
# Asset Types (UI display names — currency_precision.py ile eşleşir)
# ---------------------------------------------------------------------------
ASSET_TYPE_GOLD:        Final[str] = "Altın"
ASSET_TYPE_CRYPTO:      Final[str] = "Kripto"
ASSET_TYPE_STOCK:       Final[str] = "Hisse Senedi"
ASSET_TYPE_FUND:        Final[str] = "Yatırım Fonu"
ASSET_TYPE_REAL_ESTATE: Final[str] = "Gayrimenkul"

# ---------------------------------------------------------------------------
# Default Currency
# ---------------------------------------------------------------------------
DEFAULT_CURRENCY_CODE:   Final[str] = "TRY"
DEFAULT_CURRENCY_SYMBOL: Final[str] = "₺"

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------
__all__ = [
    "MONTH_NAMES_TR",
    "CHART_COLORS",
    "TICKER_DECIMAL_PLACES",
    "GOLD_GRAMS_PER_TROY_OUNCE",
    "TRANSACTION_TYPE_INCOME",
    "TRANSACTION_TYPE_EXPENSE",
    "TRANSACTION_TYPE_INVESTMENT",
    "TRANSACTION_TYPE_TRANSFER",
    "TRANSACTION_STATUS_PAID",
    "TRANSACTION_STATUS_PENDING",
    "PLAN_TYPE_INSTALLMENT",
    "PLAN_TYPE_SUBSCRIPTION",
    "PLAN_TYPE_DCA",
    "PLAN_TYPE_RENT",
    "PLAN_STATUS_ACTIVE",
    "PLAN_STATUS_COMPLETED",
    "PLAN_STATUS_CANCELLED",
    "ROLE_USER",
    "ROLE_TENANT_ADMIN",
    "ROLE_MANAGER",
    "ROLE_SYSTEM_ADMIN",
    "ASSET_TYPE_GOLD",
    "ASSET_TYPE_CRYPTO",
    "ASSET_TYPE_STOCK",
    "ASSET_TYPE_FUND",
    "ASSET_TYPE_REAL_ESTATE",
    "DEFAULT_CURRENCY_CODE",
    "DEFAULT_CURRENCY_SYMBOL",
]
