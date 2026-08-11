import sqlite3
import os
import sys

def migrate_oauth():
    # Proje kök dizinini bul
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    db_path = os.path.join(root_dir, 'e_cuzdan_v15.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        sys.exit(1)
        
    print(f"Migrating database at {db_path}...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(user)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # 1. auth_provider
        if 'auth_provider' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN auth_provider VARCHAR(20) NOT NULL DEFAULT 'LOCAL'")
            print("Added auth_provider column.")
            
        # 2. oauth_id
        if 'oauth_id' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN oauth_id VARCHAR(100) DEFAULT NULL")
            print("Added oauth_id column.")
            
        # 3. avatar_url
        if 'avatar_url' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN avatar_url VARCHAR(500) DEFAULT NULL")
            print("Added avatar_url column.")
            
        # 4. email_verified
        if 'email_verified' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT 0")
            print("Added email_verified column.")
            
        # 5. last_login_at
        if 'last_login_at' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN last_login_at DATETIME DEFAULT NULL")
            print("Added last_login_at column.")
            
        # 6. created_via
        if 'created_via' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN created_via VARCHAR(50) NOT NULL DEFAULT 'web'")
            print("Added created_via column.")

        print("Committing changes...")
        conn.commit()
        print("Migration successful!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_oauth()
