"""
Log Retention Policy - Log dosyalarının otomatik temizlenmesi ve arşivlenmesi
"""

import os
import shutil
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import gzip


class LogRetentionConfig:
    """Log retention konfigürasyonu"""
    
    def __init__(self):
        # Retention süreleri (gün)
        self.detailed_logs_retention_days = 30
        self.error_logs_retention_days = 90
        self.security_logs_retention_days = 365
        
        # Dosya boyut limitleri (MB)
        self.max_log_size_mb = 100
        self.max_total_log_size_mb = 500
        
        # Arşivleme ayarları
        self.enable_compression = True
        self.archive_dir = 'logs/archive'
        
        # Otomatik temizleme
        self.auto_cleanup_enabled = True


class LogRetentionManager:
    """Log retention yöneticisi"""
    
    def __init__(self, config: LogRetentionConfig = None):
        self.config = config or LogRetentionConfig()
        self.logger = logging.getLogger(__name__)
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    
    def cleanup_old_logs(self):
        """Eski log dosyalarını temizle"""
        if not self.config.auto_cleanup_enabled:
            self.logger.info("Auto cleanup disabled")
            return
        
        try:
            # Log dosyalarını bul
            log_files = self._get_log_files()
            
            for log_file in log_files:
                file_age_days = self._get_file_age_days(log_file['path'])
                retention_days = self._get_retention_days(log_file['type'])
                
                if file_age_days > retention_days:
                    self._archive_or_delete(log_file['path'], file_age_days)
            
            self.logger.info("Log cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Log cleanup failed: {e}")
    
    def _get_log_files(self) -> List[Dict]:
        """Log dosyalarını listele"""
        log_files = []
        
        log_types = {
            'e_cuzdan.log': 'detailed',
            'e_cuzdan_structured.log': 'detailed',
            'e_cuzdan_errors.log': 'error',
            'e_cuzdan_errors_structured.log': 'error',
            'e_cuzdan_security.log': 'security',
        }
        
        for filename, log_type in log_types.items():
            file_path = os.path.join(self.log_dir, filename)
            if os.path.exists(file_path):
                log_files.append({
                    'path': file_path,
                    'type': log_type,
                    'filename': filename
                })
        
        # Rotasyon dosyalarını da ekle (.1, .2, .gz vb.)
        for filename in os.listdir(self.log_dir):
            if filename.startswith('e_cuzdan') and filename.endswith(('.1', '.2', '.3', '.4', '.5', '.gz')):
                file_path = os.path.join(self.log_dir, filename)
                log_type = 'error' if 'error' in filename else ('security' if 'security' in filename else 'detailed')
                log_files.append({
                    'path': file_path,
                    'type': log_type,
                    'filename': filename
                })
        
        return log_files
    
    def _get_file_age_days(self, file_path: str) -> int:
        """Dosya yaşını gün olarak hesapla"""
        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        file_age = datetime.now() - file_mtime
        return file_age.days
    
    def _get_retention_days(self, log_type: str) -> int:
        """Log tipi için retention süresi"""
        retention_map = {
            'detailed': self.config.detailed_logs_retention_days,
            'error': self.config.error_logs_retention_days,
            'security': self.config.security_logs_retention_days
        }
        return retention_map.get(log_type, 30)
    
    def _archive_or_delete(self, file_path: str, file_age_days: int):
        """Dosyayı arşivle veya sil"""
        try:
            if self.config.enable_compression and file_age_days > 7:
                self._compress_and_archive(file_path)
            else:
                os.remove(file_path)
                self.logger.info(f"Deleted old log: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to archive/delete {file_path}: {e}")
    
    def _compress_and_archive(self, file_path: str):
        """Dosyayı sıkıştır ve arşivle"""
        try:
            # Arşiv dizini oluştur
            archive_dir = os.path.join(self.log_dir, self.config.archive_dir)
            os.makedirs(archive_dir, exist_ok=True)
            
            # Dosya adı oluştur
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime('%Y%m%d')
            archive_filename = f"{filename}.{timestamp}.gz"
            archive_path = os.path.join(archive_dir, archive_filename)
            
            # Sıkıştır
            with open(file_path, 'rb') as f_in:
                with gzip.open(archive_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Orijinal dosyayı sil
            os.remove(file_path)
            
            self.logger.info(f"Archived log: {file_path} -> {archive_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to compress {file_path}: {e}")
    
    def check_disk_space(self):
        """Disk alanını kontrol et ve gerekirse temizle"""
        try:
            import shutil
            
            total_log_size = 0
            for filename in os.listdir(self.log_dir):
                file_path = os.path.join(self.log_dir, filename)
                if os.path.isfile(file_path):
                    total_log_size += os.path.getsize(file_path)
            
            total_log_size_mb = total_log_size / (1024 * 1024)
            
            if total_log_size_mb > self.config.max_total_log_size_mb:
                self.logger.warning(f"Log size exceeds limit: {total_log_size_mb:.2f}MB")
                self.cleanup_old_logs()
                
        except Exception as e:
            self.logger.error(f"Disk space check failed: {e}")
    
    def get_log_stats(self) -> Dict:
        """Log istatistiklerini getir"""
        try:
            stats = {
                'total_files': 0,
                'total_size_mb': 0,
                'files_by_type': {
                    'detailed': {'count': 0, 'size_mb': 0},
                    'error': {'count': 0, 'size_mb': 0},
                    'security': {'count': 0, 'size_mb': 0},
                    'archive': {'count': 0, 'size_mb': 0}
                }
            }
            
            for filename in os.listdir(self.log_dir):
                file_path = os.path.join(self.log_dir, filename)
                if os.path.isfile(file_path):
                    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    stats['total_files'] += 1
                    stats['total_size_mb'] += file_size_mb
                    
                    if 'archive' in filename or '.gz' in filename:
                        stats['files_by_type']['archive']['count'] += 1
                        stats['files_by_type']['archive']['size_mb'] += file_size_mb
                    elif 'error' in filename:
                        stats['files_by_type']['error']['count'] += 1
                        stats['files_by_type']['error']['size_mb'] += file_size_mb
                    elif 'security' in filename:
                        stats['files_by_type']['security']['count'] += 1
                        stats['files_by_type']['security']['size_mb'] += file_size_mb
                    else:
                        stats['files_by_type']['detailed']['count'] += 1
                        stats['files_by_type']['detailed']['size_mb'] += file_size_mb
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Log stats calculation failed: {e}")
            return {}


# Global instance
_log_retention_manager = None


def get_log_retention_manager() -> LogRetentionManager:
    """Global log retention manager instance'ı al"""
    global _log_retention_manager
    if _log_retention_manager is None:
        _log_retention_manager = LogRetentionManager()
    return _log_retention_manager


def setup_log_retention(config: LogRetentionConfig = None):
    """Log retention sistemini konfigüre et"""
    global _log_retention_manager
    _log_retention_manager = LogRetentionManager(config)
    return _log_retention_manager
