#!/usr/bin/env python3
"""E-Cüzdan — Güvenli Önbellek ve Geçici Dosya Temizleyici (scripts/clean_caches.py).

Programın çalışma mantığına, kaynak kodlarına ve aktif veritabanına zarar vermeden
geçici önbellekleri, eski import snapshot'larını, HTML test raporlarını ve
derlenmiş .pyc bytecode dosyalarını temizler.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def get_dir_size(path: Path) -> int:
    """Klasörün toplam boyutunu byte cinsinden döner."""
    total = 0
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    for root, _, files in os.walk(path):
        for f in files:
            fp = Path(root) / f
            try:
                total += fp.stat().st_size
            except OSError:
                pass
    return total


def format_size(bytes_val: int) -> str:
    """Byte değerini okunabilir MB formatına çevirir."""
    return f"{bytes_val / (1024 * 1024):.2f} MB"


def clean_target_dir(target: Path, name: str) -> int:
    """Belirtilen dizini siler ve kurtarılan boyutu döner."""
    if not target.exists():
        return 0
    size = get_dir_size(target)
    try:
        shutil.rmtree(target)
        print(f"  [OK] Silindi: {name} ({format_size(size)})")
        return size
    except Exception as e:
        print(f"  [UYARI] Silinemedi ({name}): {e}")
        return 0


def clean_pycache(root_dir: Path) -> int:
    """Tüm __pycache__ dizinlerini ve .pyc dosyalarını siler."""
    total_freed = 0
    count = 0
    for dirpath, dirnames, _ in os.walk(root_dir, topdown=False):
        if "__pycache__" in dirnames:
            pycache_dir = Path(dirpath) / "__pycache__"
            size = get_dir_size(pycache_dir)
            try:
                shutil.rmtree(pycache_dir)
                total_freed += size
                count += 1
            except Exception:
                pass

    print(f"  [OK] Temizlendi: {count} adet __pycache__ klasörü ({format_size(total_freed)})")
    return total_freed


def clean_work_snapshots() -> int:
    """Eski geçici .work/snapshots/*.db dosyalarını temizler."""
    snapshots_dir = REPO_ROOT / ".work" / "snapshots"
    if not snapshots_dir.exists():
        return 0

    total_freed = 0
    count = 0
    for db_file in snapshots_dir.glob("*.db"):
        try:
            size = db_file.stat().st_size
            db_file.unlink()
            total_freed += size
            count += 1
        except Exception as e:
            print(f"  [UYARI] Snapshot silinemedi ({db_file.name}): {e}")

    print(f"  [OK] Temizlendi: {count} adet geçici DB snapshot ({format_size(total_freed)})")
    return total_freed


def rotate_backups() -> int:
    """Eski Eylül ayı ara snapshot'larını temizler, en son yedeği ve baseline'ı korur."""
    backups_dir = REPO_ROOT / "backups"
    if not backups_dir.exists():
        return 0

    # Korunacaklar: clean_baseline_snapshot.db ve en yeni maintenance_snapshot
    maintenance_files = sorted(backups_dir.glob("maintenance_snapshot_*.db"))
    if len(maintenance_files) <= 1:
        return 0

    # En sonuncuyu hariç tut, eskileri sil
    to_delete = maintenance_files[:-1]
    total_freed = 0
    for bf in to_delete:
        try:
            size = bf.stat().st_size
            bf.unlink()
            total_freed += size
            print(f"  [OK] Eski yedek rotasyonu: {bf.name} ({format_size(size)})")
        except Exception as e:
            print(f"  [UYARI] Yedek silinemedi ({bf.name}): {e}")

    return total_freed


def clean_adhoc_backups() -> int:
    """backups/ içerisindeki eski .bak dosyalarını temizler."""
    backups_dir = REPO_ROOT / "backups"
    if not backups_dir.exists():
        return 0

    total_freed = 0
    for bak_file in backups_dir.glob("*.bak*"):
        try:
            size = bak_file.stat().st_size
            bak_file.unlink()
            total_freed += size
            print(f"  [OK] Eski ad-hoc yedek silindi: {bak_file.name} ({format_size(size)})")
        except Exception as e:
            print(f"  [UYARI] Yedek silinemedi ({bak_file.name}): {e}")

    return total_freed


def clean_test_databases() -> int:
    """instance/ içerisindeki geçici test veritabanlarını ve fuzz marker dosyalarını temizler."""
    instance_dir = REPO_ROOT / "instance"
    if not instance_dir.exists():
        return 0

    total_freed = 0
    count_db = 0
    count_ts = 0

    # 1. Test ve repro veritabanları
    test_db_patterns = ["e_cuzdan_test_*.db", "test_*.db", "test_repro_*.db", "backup_v*.db"]
    for pat in test_db_patterns:
        for db_file in instance_dir.glob(pat):
            try:
                size = db_file.stat().st_size
                db_file.unlink()
                total_freed += size
                count_db += 1
            except Exception as e:
                print(f"  [UYARI] Test DB silinemedi ({db_file.name}): {e}")

    # 2. Test fuzz invalidation marker'ları
    for ts_pattern in [
        ".cache_inv_fuzz_*.ts",
        ".cache_inv_tenant_*.ts",
        ".cache_inv_test_*.ts",
        ".cache_inv_tx-*.ts",
        ".cache_inv_plan-*.ts",
    ]:
        for ts_file in instance_dir.glob(ts_pattern):
            try:
                size = ts_file.stat().st_size
                ts_file.unlink()
                total_freed += size
                count_ts += 1
            except Exception:
                pass

    # 3. Geçici diagnostics ve pytest_logs klasörleri
    for sub in ["diagnostics", "pytest_logs"]:
        sub_path = instance_dir / sub
        if sub_path.exists():
            total_freed += clean_target_dir(sub_path, f"instance/{sub}/")

    if count_db > 0 or count_ts > 0:
        print(f"  [OK] Temizlendi: {count_db} test DB, {count_ts} geçici invalidation marker ({format_size(total_freed)})")
    return total_freed


def clean_log_and_report_artifacts() -> int:
    """logs/ klasöründeki eski arşiv zip'lerini, audit raporlarını ve büyük logları temizler."""
    logs_dir = REPO_ROOT / "logs"
    total_freed = 0

    # 1. logs/archive klasörü
    archive_dir = logs_dir / "archive"
    if archive_dir.exists():
        total_freed += clean_target_dir(archive_dir, "logs/archive/")

    # 2. Eski audit raporları
    for r in logs_dir.glob("audit_*.json"):
        try:
            size = r.stat().st_size
            r.unlink()
            total_freed += size
            print(f"  [OK] Eski audit raporu silindi: {r.name} ({format_size(size)})")
        except Exception:
            pass

    # 3. Kök dizindeki geçici .coverage dosyası
    cov_file = REPO_ROOT / ".coverage"
    if cov_file.exists():
        try:
            size = cov_file.stat().st_size
            cov_file.unlink()
            total_freed += size
            print(f"  [OK] Geçici test coverage verisi silindi: .coverage ({format_size(size)})")
        except Exception:
            pass

    # 4. Aktif log dosyalarını sıfırla (truncate)
    for log_file in logs_dir.glob("*.log"):
        try:
            size = log_file.stat().st_size
            if size > 0:
                with open(log_file, "w", encoding="utf-8") as f:
                    f.truncate(0)
                total_freed += size
                print(f"  [OK] Log dosyası sıfırlandı: {log_file.name} ({format_size(size)})")
        except Exception:
            pass

    return total_freed


def optimize_sqlite_databases() -> int:
    """Aktif SQLite veritabanlarında VACUUM ve PRAGMA optimize çalıştırarak parçalanmayı giderir."""
    import sqlite3

    db_candidates = list(REPO_ROOT.glob("e_cuzdan_v*.db"))
    instance_dir = REPO_ROOT / "instance"
    if instance_dir.exists():
        db_candidates.extend(instance_dir.glob("*.db"))

    total_freed = 0
    for db_path in db_candidates:
        if not db_path.is_file():
            continue
        try:
            size_before = db_path.stat().st_size
            conn = sqlite3.connect(str(db_path))
            conn.execute("VACUUM;")
            conn.execute("PRAGMA optimize;")
            conn.close()
            size_after = db_path.stat().st_size
            diff = size_before - size_after
            if diff > 0:
                total_freed += diff
                print(f"  [OK] SQLite VACUUM tamamlandı: {db_path.name} (Kurtarılan: {format_size(diff)})")
            else:
                print(f"  [OK] SQLite optimize edildi: {db_path.name} (Zaten kompakt)")
        except Exception as e:
            print(f"  [UYARI] SQLite optimize edilemedi ({db_path.name}): {e}")

    return total_freed


def run_cleanup(
    include_node_modules: bool = True,
    include_backup_rotation: bool = True,
    include_sqlite_vacuum: bool = True,
) -> None:
    print("============================================================")
    print("  E-CÜZDAN GÜVENLİ DİSK VE ÖNBELLEK TEMİZLEYİCİ")
    print("============================================================")

    initial_size = get_dir_size(REPO_ROOT)
    print(f"Başlangıç Proje Boyutu: {format_size(initial_size)}\n")

    total_freed = 0

    # 1. HTML Coverage
    print("[1/9] Test Coverage Raporları:")
    total_freed += clean_target_dir(REPO_ROOT / "htmlcov", "htmlcov/")

    # 2. Araç Önbellekleri
    print("\n[2/9] Linter ve Test Önbellekleri:")
    total_freed += clean_target_dir(REPO_ROOT / ".mypy_cache", ".mypy_cache/")
    total_freed += clean_target_dir(REPO_ROOT / ".pytest_cache", ".pytest_cache/")
    total_freed += clean_target_dir(REPO_ROOT / ".ruff_cache", ".ruff_cache/")

    # 3. Geçici .work Snapshot'ları
    print("\n[3/9] Geçici Çalışma Alanı Snapshot'ları:")
    total_freed += clean_work_snapshots()

    # 4. __pycache__ ve derlenmiş bytecode'lar (Tüm repo + .venv)
    print("\n[4/9] Python Bytecode ve __pycache__ Önbellekleri:")
    total_freed += clean_pycache(REPO_ROOT)

    # 5. İsteğe Bağlı: node_modules
    if include_node_modules:
        print("\n[5/9] Derleme Modülleri (node_modules):")
        total_freed += clean_target_dir(REPO_ROOT / "node_modules", "node_modules/")
    else:
        print("\n[5/9] node_modules atlandı.")

    # 6. İsteğe Bağlı: Eski backup rotasyonu
    if include_backup_rotation:
        print("\n[6/9] Eski Yedeklerin Rotasyonu:")
        total_freed += rotate_backups()
        total_freed += clean_adhoc_backups()
    else:
        print("\n[6/9] Yedek rotasyonu atlandı.")

    # 7. Geçici Test Veritabanları ve Marker Temizliği
    print("\n[7/9] Geçici Test Veritabanları ve Fuzz Marker Temizliği:")
    total_freed += clean_test_databases()

    # 8. Log Arşivleri, Eski Audit Çıktıları ve Coverage Temizliği
    print("\n[8/9] Log Arşivleri, Audit Çıktıları ve Coverage Temizliği:")
    total_freed += clean_log_and_report_artifacts()

    # 9. SQLite Veritabanı VACUUM & Optimize
    if include_sqlite_vacuum:
        print("\n[9/9] SQLite Veritabanı Defrag & VACUUM:")
        total_freed += optimize_sqlite_databases()
    else:
        print("\n[9/9] SQLite VACUUM atlandı.")

    final_size = get_dir_size(REPO_ROOT)
    print("\n============================================================")
    print("Temizlik Tamamlandı!")
    print(f"  Kurtarılan Alan: {format_size(total_freed)}")
    print(f"  Yeni Proje Boyutu: {format_size(final_size)} (Önceki: {format_size(initial_size)})")
    saved_pct = (total_freed / initial_size * 100) if initial_size else 0
    print(f"  Boyut Azalma Oranı: %{saved_pct:.1f}")
    print("============================================================")


if __name__ == "__main__":
    run_cleanup(
        include_node_modules=True,
        include_backup_rotation=True,
        include_sqlite_vacuum=True,
    )
