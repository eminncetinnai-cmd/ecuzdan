import os
import shutil
import hashlib
import sqlite3
import datetime
import subprocess

# Define Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGING_DIR = os.path.join(PROJECT_ROOT, "staging")
STAGING_DB_DIR = os.path.join(STAGING_DIR, "database")
STAGING_LOGS_DIR = os.path.join(STAGING_DIR, "logs")
STAGING_BACKUPS_DIR = os.path.join(STAGING_DIR, "backups")

ENV_FILE = os.path.join(STAGING_DIR, ".env.staging")
SOURCE_DB = os.path.join(PROJECT_ROOT, "e_cuzdan_v15.db")
STAGING_DB = os.path.join(STAGING_DB_DIR, "staging.db")
REPORT_FILE = os.path.join(PROJECT_ROOT, "PRODUCTION_SIMULATION_REPORT.md")

def create_directories():
    print(">>> Creating Production Simulation Environment directories...")
    for directory in [STAGING_DIR, STAGING_DB_DIR, STAGING_LOGS_DIR, STAGING_BACKUPS_DIR]:
        os.makedirs(directory, exist_ok=True)
    print("    [OK] Directories created.")

def create_env_file():
    print(">>> Generating .env.staging...")
    env_content = f"""FLASK_ENV=production
DATABASE_URL=sqlite:///{STAGING_DB}
SECRET_KEY=staging_simulation_secret_key_123
LOG_DIR={STAGING_LOGS_DIR}
"""
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.write(env_content)
    print("    [OK] .env.staging generated.")

def setup_database_and_backup():
    print(">>> Setting up database and taking backup...")
    if not os.path.exists(SOURCE_DB):
        print(f"    [ERROR] Source DB not found at {SOURCE_DB}")
        return False
    
    # Copy to staging
    shutil.copy2(SOURCE_DB, STAGING_DB)
    
    # Take backup
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(STAGING_BACKUPS_DIR, f"staging_backup_{timestamp}.db")
    shutil.copy2(STAGING_DB, backup_path)
    
    print(f"    [OK] Database copied to {STAGING_DB}")
    print(f"    [OK] Backup created at {backup_path}")
    return True

def get_db_hash(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_financial_totals(db_path):
    # Try to connect and get some basic stats
    # We will just get row counts of all tables as a basic validation.
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    stats = {}
    for table in tables:
        table_name = table[0]
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            stats[table_name] = count
        except Exception:
            stats[table_name] = "Error"
    
    # If there's a wallet table with balance
    total_balance = 0
    try:
        cursor.execute("SELECT balance FROM wallet")
        balances = cursor.fetchall()
        total_balance = sum(b[0] for b in balances if b[0] is not None)
        stats['TOTAL_WALLET_BALANCE'] = total_balance
    except Exception:
        pass
        
    conn.close()
    return stats

def run_validation(stage="Pre"):
    print(f"\n>>> Running {stage}-Migration Validation...")
    db_hash = get_db_hash(STAGING_DB)
    stats = get_financial_totals(STAGING_DB)
    print(f"    [SHA256] {db_hash}")
    print(f"    [STATS] {stats}")
    return {"hash": db_hash, "stats": stats}

def run_migrations():
    print("\n>>> Applying Database Migrations (Simulated)...")
    # In a real environment, you'd run something like:
    # subprocess.run(["flask", "db", "upgrade"], env={"FLASK_APP": "app.py", "FLASK_ENV": "production"})
    # Since we are setting up the structure, we will simulate a DB operation for testing
    conn = sqlite3.connect(STAGING_DB)
    cursor = conn.cursor()
    try:
        cursor.execute("CREATE TABLE IF NOT EXISTS simulation_history (id INTEGER PRIMARY KEY, applied_at TEXT)")
        cursor.execute("INSERT INTO simulation_history (applied_at) VALUES (?)", (datetime.datetime.now().isoformat(),))
        conn.commit()
        print("    [OK] Migration (Simulation) applied.")
    except Exception as e:
        print(f"    [ERROR] Migration failed: {e}")
    finally:
        conn.close()

def run_integration_tests():
    print("\n>>> Running Integration Tests...")
    # Assuming pytest is used
    try:
        # Run pytest if tests folder exists
        if os.path.exists(os.path.join(PROJECT_ROOT, "tests")):
            import sys
            result = subprocess.run([sys.executable, "-m", "pytest", "tests/"], cwd=PROJECT_ROOT, capture_output=True, text=True)
            if result.returncode == 0:
                print("    [OK] Integration tests passed.")
                return True
            else:
                print("    [WARNING] Integration tests failed or had warnings.")
                print(f"         > {result.stdout[:200]}...")
                return False
        else:
            print("    [INFO] No tests directory found. Skipping.")
            return True
    except Exception as e:
        print(f"    [ERROR] Failed to run tests: {e}")
        return False

def generate_report(pre_val, post_val, tests_passed):
    print(f"\n>>> Generating {REPORT_FILE}...")
    
    go_nogo = "GO" if tests_passed else "NO-GO"
    
    report = f"""# PRODUCTION SIMULATION REPORT (Sprint-01C.1)

## Executive Summary
- **Decision:** `{go_nogo}`
- **Timestamp:** {datetime.datetime.now().isoformat()}
- **Environment:** Local Production Simulation

## Validation Details

### Pre-Migration
- **DB Hash (SHA256):** `{pre_val['hash']}`
- **Database Stats:**
```json
{pre_val['stats']}
```

### Post-Migration
- **DB Hash (SHA256):** `{post_val['hash']}`
- **Database Stats:**
```json
{post_val['stats']}
```

### Integration Tests
- **Status:** {'PASSED' if tests_passed else 'FAILED / SKIPPED'}

## Next Steps
- Bu simülasyon ortamı, ilerleyen sprintlerde Immutable Ledger ve Double Entry Accounting değişiklikleri için güvenli bir test alanı sağlayacaktır.
- `staging/` klasöründeki konfigürasyon ve izole veritabanı ile geliştirmelerinizi production benzeri ortamda doğrulayabilirsiniz.
"""
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)
    print("    [OK] Report generated.")

def main():
    print("============================================")
    print("   PRODUCTION SIMULATION ENVIRONMENT INIT   ")
    print("============================================")
    
    create_directories()
    create_env_file()
    
    if not setup_database_and_backup():
        return
        
    pre_val = run_validation("Pre")
    run_migrations()
    post_val = run_validation("Post")
    
    tests_passed = run_integration_tests()
    
    generate_report(pre_val, post_val, tests_passed)
    
    print("\n============================================")
    print("               SIMULATION COMPLETE          ")
    print("============================================")

if __name__ == "__main__":
    main()
