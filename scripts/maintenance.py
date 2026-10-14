#!/usr/bin/env python3
"""E-Cüzdan CLI Veritabanı Bakım ve Sağlık Aracı (scripts/maintenance.py).

Web sunucusuna bağımlı olmadan, SQLite veritabanı üzerinde:
  - Bütünlük kontrolü (PRAGMA integrity_check)
  - Anlık güvenlik yedeği ve rotasyon (en güncel 3 yedek tutulur)
  - WAL günlüğü checkpoint & sıfırlama (PRAGMA wal_checkpoint(TRUNCATE))
  - Defragmentasyon ve boş alan iadesi (VACUUM)
  - Sorgu planlayıcı istatistik optimizasyonu (PRAGMA optimize)
işlemlerini tek komutla veya zamanlanmış görev (Cron / Task Scheduler) olarak çalıştırır.

Kullanım:
  python scripts/maintenance.py --status     (Sadece veritabanı durumunu ve boyutlarını gösterir)
  python scripts/maintenance.py --execute    (Tam bakım boru hattını çalıştırır)
  python scripts/maintenance.py --no-snapshot (Yedek almadan doğrudan optimize eder)
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Proje kökünü sys.path'e ekle
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from domain.storage_health.services.data_hygiene_service import (
    DataHygieneService,
    HygieneInspectionResult,
)
from domain.storage_health.services.database_maintenance import (
    DatabaseMaintenanceService,
    DatabaseStats,
)


def print_stats(stats: DatabaseStats, hygiene: HygieneInspectionResult | None = None) -> None:
    print("\n" + "=" * 60)
    print("  E-CÜZDAN VERİTABANI DURUM RAPORU")
    print("=" * 60)
    print(f"  Dosya Yolu            : {stats.db_path}")
    print(f"  Durum                 : {'Mevcut' if stats.exists else 'Bulunamadı'}")
    print(f"  Ana DB Boyutu         : {stats.size_bytes / (1024 * 1024):.2f} MB ({stats.size_bytes:,} bayt)")
    print(f"  WAL Günlük Boyutu     : {stats.wal_size_bytes / 1024:.1f} KB")
    print(f"  Toplam Boyut          : {stats.total_size_bytes / (1024 * 1024):.2f} MB")
    print(f"  Journal Modu          : {stats.journal_mode}")
    print(f"  Bütünlük Durumu       : {stats.integrity_status}")
    print(f"  Foreign Key İhlali    : {stats.foreign_key_violations}")
    print(f"  Boş Sayfa Sayısı      : {stats.freelist_count}")
    print(f"  Kurtarılabilir Alan   : {stats.reclaimable_bytes / 1024:.1f} KB")
    if hygiene:
        print("-" * 60)
        print(f"  Okunmuş Eski Bildirim : {hygiene.read_notifications_count} satır")
        print(f"  Süresi Dolan Bildirim : {hygiene.expired_notifications_count} satır")
        print(f"  İşlenmiş Outbox Mesaj : {hygiene.processed_outbox_count} satır")
        print(f"  Temizlenebilir Satır  : {hygiene.total_prunable_rows} satır")
    print("=" * 60 + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="E-Cüzdan CLI Veritabanı Bakım Aracı")
    parser.add_argument("--db", type=str, default="e_cuzdan_v15.db", help="Hedef veritabanı dosya yolu")
    parser.add_argument("--status", action="store_true", help="Yalnızca veritabanı durumunu görüntüle")
    parser.add_argument("--execute", action="store_true", help="Tam bakım boru hattını çalıştır")
    parser.add_argument("--hygiene-only", action="store_true", help="Yalnızca geçici veri temizliğini (veri hijyeni) çalıştır")
    parser.add_argument("--no-snapshot", action="store_true", help="Bakım öncesi snapshot yedeği almayı atla")
    args = parser.parse_args()

    db_file = PROJECT_ROOT / args.db
    if not db_file.exists():
        print(f"HATA: Veritabanı dosyası bulunamadı: {db_file}", file=sys.stderr)
        return 1

    service = DatabaseMaintenanceService(
        db_path=db_file,
        backup_dir=PROJECT_ROOT / "backups",
    )
    hygiene_service = DataHygieneService(db_path=db_file)

    if args.hygiene_only:
        print("\n" + "=" * 60)
        print("  GEÇİCİ VERİ HİJYENİ (PRUNING) ÇALIŞTIRILIYOR")
        print("=" * 60)
        res = hygiene_service.execute_hygiene()
        badge = "[OK]  " if res.success else "[FAIL]"
        print(f"  {badge} {res.message} ({res.duration_ms:.1f}ms)")
        print(f"  Budanan Bildirimler   : {res.notifications_pruned}")
        print(f"  Budanan Outbox Mesaj  : {res.outbox_messages_pruned}")
        print("=" * 60 + "\n")
        return 0 if res.success else 1

    if args.status or not args.execute:
        stats = service.get_stats()
        hygiene_info = hygiene_service.inspect_hygiene()
        print_stats(stats, hygiene_info)
        if not args.execute:
            print("İpucu: Bakım boru hattını çalıştırmak için '--execute' bayrağını kullanın.")
            return 0

    print("\n" + "=" * 60)
    print("  VERİTABANI BAKIM BORU HATTI BAŞLATILIYOR")
    print("=" * 60)

    # 1. Aşama: Veri hijyeni (geçici kayıt budama)
    hygiene_res = hygiene_service.execute_hygiene()
    h_badge = "[OK]  " if hygiene_res.success else "[FAIL]"
    print(f"  {h_badge} {'Operasyonel Veri Hijyeni (Budama)':<40} ({hygiene_res.duration_ms:.1f}ms) - {hygiene_res.message}")

    # 2. Aşama: Fiziksel veritabanı bakımı ve sıkıştırma
    t0 = time.monotonic()
    summary = service.execute_maintenance_pipeline(
        create_safety_snapshot=not args.no_snapshot
    )
    total_duration = time.monotonic() - t0

    for step in summary.steps:
        badge = "[OK]  " if step.success else "[FAIL]"
        print(f"  {badge} {step.title:<40} ({step.duration_ms:.1f}ms) - {step.message}")

    print("-" * 60)
    print(f"  Toplam Süre           : {total_duration:.2f} saniye")
    print(f"  Bakım Öncesi Boyut    : {summary.db_size_before / (1024 * 1024):.2f} MB")
    print(f"  Bakım Sonrası Boyut   : {summary.db_size_after / (1024 * 1024):.2f} MB")
    print(f"  Kurtarılan Alan       : {summary.bytes_freed / 1024:.1f} KB")
    print(f"  Budanan Satır Sayısı  : {hygiene_res.total_rows_pruned}")
    if summary.snapshot_path:
        print(f"  Snapshot Konumu       : {summary.snapshot_path}")
    print("=" * 60)

    if summary.success:
        print("\n[OK] Veritabani bakimi basariyla tamamlandi.\n")
        return 0
    else:
        print("\n[FAIL] Veritabani bakimi sirasinda bazi hatalar olustu.\n", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
