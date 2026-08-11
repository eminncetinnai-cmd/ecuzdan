"""
Monitoring API Routes - Log monitoring ve dashboard endpoint'leri
"""

from flask import Blueprint, jsonify, request, session, render_template
from utils.decorators import login_required
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List
import re
import time

monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/monitoring')

logger = logging.getLogger(__name__)

# Simple in-memory cache with TTL
_cache = {}
_cache_ttl = {
    'stats': 30,      # 30 seconds
    'health': 60,    # 60 seconds
    'log_files': 300 # 5 minutes
}


def _get_cache_key(key: str) -> tuple:
    """Get cached value if not expired"""
    if key in _cache:
        value, timestamp = _cache[key]
        ttl = _cache_ttl.get(key.split('_')[0], 30)
        if time.time() - timestamp < ttl:
            return value
    return None


def _set_cache(key: str, value):
    """Set cache value with current timestamp"""
    _cache[key] = (value, time.time())


def _clear_cache(pattern: str = None):
    """Clear cache entries matching pattern"""
    if pattern:
        keys_to_delete = [k for k in _cache.keys() if pattern in k]
        for key in keys_to_delete:
            del _cache[key]
    else:
        _cache.clear()


def _standard_response(success: bool, data=None, error=None):
    """
    Standart response formatı
    
    Args:
        success: İşlem başarılı mı
        data: Response verisi
        error: Hata mesajı
    
    Returns:
        Standard response dict
    """
    return {
        'success': success,
        'data': data,
        'error': error,
        'timestamp': datetime.now().isoformat()
    }


def register_monitoring_routes(bp):
    """
    Monitoring route'larını kaydeder
    
    Args:
        bp: Blueprint objesi
    """
    
    @bp.route('/')
    @login_required
    def monitoring_dashboard():
        """
        Monitoring dashboard sayfası
        """
        logger.info("Monitoring dashboard accessed")
        return render_template('monitoring.html')
    
    @bp.route('/api/stats', methods=['GET'])
    @login_required
    def monitoring_stats():
        """
        Log istatistiklerini getir
        
        Returns:
            JSON response with log statistics
        """
        try:
            logger.info("Monitoring stats API called")
            # Check cache
            cache_key = f"stats_{session.get('user_id')}"
            cached_data = _get_cache_key(cache_key)
            if cached_data:
                return jsonify(_standard_response(True, data=cached_data))
            
            log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
            
            stats = {
                'total_logs': 0,
                'error_count': 0,
                'warning_count': 0,
                'critical_count': 0,
                'security_count': 0,
                'log_files': {},
                'recent_errors': []
            }
            
            # Log dosyalarını analiz et
            log_files = {
                'e_cuzdan.log': 'main',
                'e_cuzdan_errors.log': 'errors',
                'e_cuzdan_security.log': 'security'
            }
            
            for log_file, file_type in log_files.items():
                file_path = os.path.join(log_dir, log_file)
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    stats['log_files'][file_type] = {
                        'size_bytes': file_size,
                        'size_mb': round(file_size / (1024 * 1024), 2),
                        'exists': True
                    }
                    
                    # Log satırlarını say
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            stats['total_logs'] += len(lines)
                            
                            # Son 10 hata toplama
                            if file_type == 'errors':
                                for line in lines[-10:]:
                                    if 'ERROR' in line or 'CRITICAL' in line:
                                        stats['recent_errors'].append(line.strip())
                                        if len(stats['recent_errors']) >= 5:
                                            break
                            
                            # Log seviyelerini say
                            for line in lines:
                                if 'CRITICAL' in line:
                                    stats['critical_count'] += 1
                                elif 'ERROR' in line:
                                    stats['error_count'] += 1
                                elif 'WARNING' in line:
                                    stats['warning_count'] += 1
                                elif file_type == 'security':
                                    stats['security_count'] += 1
                    except Exception as e:
                        logger.error(f"Error reading log file {log_file}: {e}")
                else:
                    stats['log_files'][file_type] = {
                        'size_bytes': 0,
                        'size_mb': 0,
                        'exists': False
                    }
            
            # Cache the result
            _set_cache(cache_key, stats)
            
            return jsonify(_standard_response(True, data=stats))
            
        except Exception as e:
            logger.error(f"Monitoring stats error: {e}")
            return jsonify(_standard_response(False, error=str(e))), 500
    
    @bp.route('/api/logs', methods=['GET'])
    @login_required
    def monitoring_logs():
        """
        Log satırlarını getir (pagination ile)
        
        Query params:
            - file: log dosyası adı (main, errors, security)
            - lines: kaç satır (default: 100)
            - level: log seviyesi filtresi (ERROR, WARNING, INFO)
            - search: arama terimi
        """
        try:
            logger.info("Monitoring logs API called")
            file_type = request.args.get('file', 'main')
            line_count = int(request.args.get('lines', 100))
            level_filter = request.args.get('level')
            search_term = request.args.get('search')
            
            log_file_map = {
                'main': 'e_cuzdan.log',
                'errors': 'e_cuzdan_errors.log',
                'security': 'e_cuzdan_security.log'
            }
            
            log_file = log_file_map.get(file_type, 'e_cuzdan.log')
            log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
            file_path = os.path.join(log_dir, log_file)
            
            if not os.path.exists(file_path):
                return jsonify({'success': False, 'error': 'Log file not found'}), 404
            
            logs = []
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                    # Filtreleme
                    filtered_lines = lines
                    if level_filter:
                        filtered_lines = [line for line in lines if level_filter in line]
                    if search_term:
                        filtered_lines = [line for line in filtered_lines if search_term.lower() in line.lower()]
                    
                    # Son satırları al
                    logs = filtered_lines[-line_count:]
                    
            except Exception as e:
                logger.error(f"Error reading log file: {e}")
                return jsonify(_standard_response(False, error=str(e))), 500
            
            return jsonify({
                'success': True,
                'data': {
                    'logs': logs,
                    'count': len(logs),
                    'file': file_type
                }
            })
            
        except Exception as e:
            logger.error(f"Monitoring logs error: {e}")
            return jsonify(_standard_response(False, error=str(e))), 500
    
    @bp.route('/api/health', methods=['GET'])
    @login_required
    def monitoring_health():
        """
        Sistem sağlık durumunu kontrol et
        
        Returns:
            JSON response with system health status
        """
        try:
            logger.info("Monitoring health API called")
            # Check cache
            cache_key = f"health_{session.get('user_id')}"
            cached_data = _get_cache_key(cache_key)
            if cached_data:
                return jsonify(_standard_response(True, data=cached_data))
            
            health_status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'components': {
                    'database': 'unknown',
                    'logs': 'unknown',
                    'disk_space': 'unknown'
                },
                'issues': []
            }
            
            # Database kontrolü
            try:
                from models import db
                db.session.execute(db.text('SELECT 1'))
                health_status['components']['database'] = 'healthy'
            except Exception as e:
                health_status['components']['database'] = 'unhealthy'
                health_status['issues'].append(f'Database connection failed: {str(e)}')
                health_status['status'] = 'degraded'
            
            # Log dosyaları kontrolü
            try:
                log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
                if os.path.exists(log_dir):
                    health_status['components']['logs'] = 'healthy'
                else:
                    health_status['components']['logs'] = 'unhealthy'
                    health_status['issues'].append('Logs directory not found')
                    health_status['status'] = 'degraded'
            except Exception as e:
                health_status['components']['logs'] = 'unhealthy'
                health_status['issues'].append(f'Logs check failed: {str(e)}')
                health_status['status'] = 'degraded'
            
            # Disk alanı kontrolü
            try:
                import shutil
                disk_usage = shutil.disk_usage(os.path.dirname(os.path.dirname(__file__)))
                free_percent = (disk_usage.free / disk_usage.total) * 100
                
                if free_percent < 10:
                    health_status['components']['disk_space'] = 'critical'
                    health_status['issues'].append(f'Low disk space: {free_percent:.1f}% free')
                    health_status['status'] = 'critical'
                elif free_percent < 20:
                    health_status['components']['disk_space'] = 'warning'
                    health_status['issues'].append(f'Low disk space: {free_percent:.1f}% free')
                    if health_status['status'] == 'healthy':
                        health_status['status'] = 'degraded'
                else:
                    health_status['components']['disk_space'] = 'healthy'
                    
                health_status['disk_usage'] = {
                    'total_gb': round(disk_usage.total / (1024**3), 2),
                    'used_gb': round(disk_usage.used / (1024**3), 2),
                    'free_gb': round(disk_usage.free / (1024**3), 2),
                    'free_percent': round(free_percent, 1)
                }
            except Exception as e:
                health_status['components']['disk_space'] = 'unknown'
                health_status['issues'].append(f'Disk space check failed: {str(e)}')
            
            # Cache the result
            _set_cache(cache_key, health_status)
            
            return jsonify(_standard_response(True, data=health_status))
            
        except Exception as e:
            logger.error(f"Monitoring health error: {e}")
            return jsonify(_standard_response(False, error=str(e))), 500
    
    @bp.route('/api/alerts/config', methods=['GET', 'POST'])
    @login_required
    def monitoring_alerts_config():
        """
        Alert konfigürasyonunu getir veya güncelle
        
        GET: Mevcut konfigürasyonu getir
        POST: Konfigürasyonu güncelle
        """
        try:
            if 'user_id' not in session:
                return jsonify(_standard_response(False, error='Unauthorized')), 401
            
            if request.method == 'GET':
                # Mevcut konfigürasyonu getir (placeholder)
                config = {
                    'email_alerts_enabled': False,
                    'smtp_server': None,
                    'from_email': None,
                    'to_emails': [],
                    'alert_thresholds': {
                        'error_rate': 10,  # errors per minute
                        'critical_rate': 1,  # critical per minute
                        'disk_space_percent': 10
                    }
                }
                return jsonify(_standard_response(True, data=config))
            
            elif request.method == 'POST':
                # Konfigürasyonu güncelle (placeholder)
                data = request.get_json()
                # TODO: Konfigürasyon kaydetme
                return jsonify(_standard_response(True, data={'message': 'Configuration updated'}))
            
        except Exception as e:
            logger.error(f"Monitoring alerts config error: {e}")
            return jsonify(_standard_response(False, error=str(e))), 500


# Blueprint kayıt fonksiyonu
def register_monitoring_routes_bp():
    """Monitoring blueprint'ini döndür"""
    return monitoring_bp
