import logging
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from sqlalchemy import text

from shared.db import db

logger = logging.getLogger("Migration_Sprint17")


def run_sprint17_migration():
    """Finansal eğitim için progress tracking ve quiz sistemini ekler (SQLite tam uyumlu)"""
    logger.info("Sprint 17 Education Migration Başlatılıyor...")

    with db.engine.connect() as conn:
        # 1. UserProgress tablosunu oluştur
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    topic VARCHAR(100) NOT NULL,
                    phase VARCHAR(50) NOT NULL,
                    completed BOOLEAN DEFAULT 0 NOT NULL,
                    progress_percent INTEGER DEFAULT 0 NOT NULL,
                    last_accessed_at DATETIME,
                    completed_at DATETIME,
                    tenant_id VARCHAR(50) NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES user(id),
                    FOREIGN KEY (tenant_id) REFERENCES tenant(id),
                    UNIQUE(user_id, topic)
                )
            """))
            logger.info("user_progress tablosu oluşturuldu")
        except Exception as e:
            logger.warning(f"user_progress tablosu zaten var veya oluşturulamadı: {e}")

        # 2. QuizAttempt tablosunu oluştur
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS quiz_attempt (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    difficulty VARCHAR(20) NOT NULL,
                    score INTEGER NOT NULL,
                    total_questions INTEGER NOT NULL,
                    correct_answers INTEGER NOT NULL,
                    completed_at DATETIME,
                    tenant_id VARCHAR(50) NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES user(id),
                    FOREIGN KEY (tenant_id) REFERENCES tenant(id)
                )
            """))
            logger.info("quiz_attempt tablosu oluşturuldu")
        except Exception as e:
            logger.warning(f"quiz_attempt tablosu zaten var veya oluşturulamadı: {e}")

        # 3. UserAchievement tablosunu oluştur
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_achievement (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    achievement_type VARCHAR(50) NOT NULL,
                    earned_at DATETIME,
                    tenant_id VARCHAR(50) NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES user(id),
                    FOREIGN KEY (tenant_id) REFERENCES tenant(id),
                    UNIQUE(user_id, achievement_type)
                )
            """))
            logger.info("user_achievement tablosu oluşturuldu")
        except Exception as e:
            logger.warning(f"user_achievement tablosu zaten var veya oluşturulamadı: {e}")

        # 4. QuizQuestion tablosunu oluştur
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS quiz_question (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    options JSON NOT NULL,
                    correct_answer VARCHAR(1) NOT NULL,
                    explanation TEXT,
                    difficulty VARCHAR(20) NOT NULL,
                    topic VARCHAR(100) NOT NULL,
                    tenant_id VARCHAR(50),
                    is_active BOOLEAN DEFAULT 1 NOT NULL,
                    FOREIGN KEY (tenant_id) REFERENCES tenant(id)
                )
            """))
            logger.info("quiz_question tablosu oluşturuldu")
        except Exception as e:
            logger.warning(f"quiz_question tablosu zaten var veya oluşturulamadı: {e}")

        # 5. Index'leri oluştur
        indexes = [
            ("idx_user_progress_user", "CREATE INDEX IF NOT EXISTS idx_user_progress_user ON user_progress(user_id)"),
            ("idx_user_progress_topic", "CREATE INDEX IF NOT EXISTS idx_user_progress_topic ON user_progress(topic)"),
            ("idx_user_progress_tenant", "CREATE INDEX IF NOT EXISTS idx_user_progress_tenant ON user_progress(tenant_id)"),
            ("idx_quiz_attempt_user", "CREATE INDEX IF NOT EXISTS idx_quiz_attempt_user ON quiz_attempt(user_id)"),
            ("idx_quiz_attempt_difficulty", "CREATE INDEX IF NOT EXISTS idx_quiz_attempt_difficulty ON quiz_attempt(difficulty)"),
            ("idx_quiz_attempt_tenant", "CREATE INDEX IF NOT EXISTS idx_quiz_attempt_tenant ON quiz_attempt(tenant_id)"),
            ("idx_user_achievement_user", "CREATE INDEX IF NOT EXISTS idx_user_achievement_user ON user_achievement(user_id)"),
            ("idx_user_achievement_type", "CREATE INDEX IF NOT EXISTS idx_user_achievement_type ON user_achievement(achievement_type)"),
            ("idx_user_achievement_tenant", "CREATE INDEX IF NOT EXISTS idx_user_achievement_tenant ON user_achievement(tenant_id)"),
            ("idx_quiz_question_difficulty", "CREATE INDEX IF NOT EXISTS idx_quiz_question_difficulty ON quiz_question(difficulty)"),
            ("idx_quiz_question_topic", "CREATE INDEX IF NOT EXISTS idx_quiz_question_topic ON quiz_question(topic)"),
            ("idx_quiz_question_tenant", "CREATE INDEX IF NOT EXISTS idx_quiz_question_tenant ON quiz_question(tenant_id)"),
        ]

        for index_name, sql in indexes:
            try:
                conn.execute(text(sql))
                logger.info(f"Index oluşturuldu: {index_name}")
            except Exception as e:
                logger.warning(f"Index zaten var veya oluşturulamadı: {index_name} -> {e}")

        conn.commit()

    logger.info("Sprint 17 Education Migration Başarıyla Tamamlandı.")


if __name__ == "__main__":
    from app import app
    with app.app_context():
        run_sprint17_migration()
