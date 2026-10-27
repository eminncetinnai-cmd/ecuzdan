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
    print("[1/7] Test Coverage Raporları:")
    total_freed += clean_target_dir(REPO_ROOT / "htmlcov", "htmlcov/")

    # 2. Araç Önbellekleri
    print("\n[2/7] Linter ve Test Önbellekleri:")
    total_freed += clean_target_dir(REPO_ROOT / ".mypy_cache", ".mypy_cache/")
    total_freed += clean_target_dir(REPO_ROOT / ".pytest_cache", ".pytest_cache/")
    total_freed += clean_target_dir(REPO_ROOT / ".ruff_cache", ".ruff_cache/")

    # 3. Geçici .work Snapshot'ları
    print("\n[3/7] Geçici Çalışma Alanı Snapshot'ları:")
    total_freed += clean_work_snapshots()

    # 4. __pycache__ ve derlenmiş bytecode'lar (Tüm repo + .venv)
    print("\n[4/7] Python Bytecode ve __pycache__ Önbellekleri:")
    total_freed += clean_pycache(REPO_ROOT)

    # 5. İsteğe Bağlı: node_modules
    if include_node_modules:
        print("\n[5/7] Derleme Modülleri (node_modules):")
        total_freed += clean_target_dir(REPO_ROOT / "node_modules", "node_modules/")
    else:
        print("\n[5/7] node_modules atlandı.")

    # 6. İsteğe Bağlı: Eski backup rotasyonu
    if include_backup_rotation:
        print("\n[6/7] Eski Yedeklerin Rotasyonu:")
        total_freed += rotate_backups()
    else:
        print("\n[6/7] Yedek rotasyonu atlandı.")

    # 7. SQLite Veritabanı VACUUM & Optimize
    if include_sqlite_vacuum:
        print("\n[7/7] SQLite Veritabanı Defrag & VACUUM:")
        total_freed += optimize_sqlite_databases()
    else:
        print("\n[7/7] SQLite VACUUM atlandı.")

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
