"""
Monitoring API Routes - Log monitoring ve dashboard endpoint'leri
"""

import logging
import os
import re  # noqa: F401
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List  # noqa: F401

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from infrastructure.i18n import i18n
from utils.capabilities import Capability, has_capability
from utils.decorators import login_required
from utils.log_viewer import is_structured_log_file, read_log_entries

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


def _monitoring_log_dir() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')


def _collect_log_stats(log_dir: str = None) -> dict:
    if log_dir is None:
        log_dir = _monitoring_log_dir()

    log_files = {
        'e_cuzdan.log': 'main',
        'e_cuzdan_structured.log': 'structured',
        'e_cuzdan_errors.log': 'errors',
        'e_cuzdan_errors_structured.log': 'errors_structured',
        'e_cuzdan_security.log': 'security',
    }

    stats = {
        'severity_source': 'structured',
        'total_logs': 0,
        'error_count': 0,
        'warning_count': 0,
        'critical_count': 0,
        'security_count': 0,
        'error_count_24h': 0,
        'warning_count_24h': 0,
        'log_files': {},
        'recent_errors': [],
        'timeline': [],
    }

    for log_file, file_type in log_files.items():
        file_path = os.path.join(log_dir, log_file)
        exists = os.path.exists(file_path)
        file_size = os.path.getsize(file_path) if exists else 0
        stats['log_files'][file_type] = {
            'size_bytes': file_size,
            'size_mb': round(file_size / (1024 * 1024), 2),
            'exists': exists,
            'levels': {'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'CRITICAL': 0},
        }

    now_utc = datetime.now(timezone.utc)
    cutoff_24h = now_utc - timedelta(hours=24)
    hourly_buckets = {}
    for h in range(23, -1, -1):
        bucket_time = (now_utc - timedelta(hours=h)).replace(minute=0, second=0, microsecond=0)
        key = bucket_time.strftime('%Y-%m-%dT%H:00:00')
        hourly_buckets[key] = {
            'timestamp': key,
            'label': bucket_time.strftime('%H:00'),
            'hour': bucket_time.strftime('%H:00'),
            'INFO': 0,
            'WARNING': 0,
            'ERROR': 0,
            'CRITICAL': 0,
        }

    structured_path = os.path.join(log_dir, 'e_cuzdan_structured.log')
    if os.path.exists(structured_path):
        try:
            with open(structured_path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    stats['total_logs'] += 1
                    try:
                        import json
                        data = json.loads(line)
                        lvl = str(data.get('level', 'INFO')).upper()
                        if lvl in stats['log_files']['structured']['levels']:
                            stats['log_files']['structured']['levels'][lvl] += 1

                        is_within_24h = False
                        ts_str = data.get('timestamp')
                        dt = None
                        if ts_str:
                            try:
                                dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                                if dt.tzinfo is None:
                                    dt = dt.replace(tzinfo=timezone.utc)
                                if dt >= cutoff_24h:
                                    is_within_24h = True
                            except Exception:
                                pass

                        if is_within_24h and dt:
                            try:
                                b_key = dt.strftime('%Y-%m-%dT%H:00:00')
                                if b_key in hourly_buckets and lvl in hourly_buckets[b_key]:
                                    hourly_buckets[b_key][lvl] += 1
                            except Exception:
                                pass

                        if lvl == 'ERROR':
                            stats['error_count'] += 1
                            if is_within_24h:
                                stats['error_count_24h'] += 1
                        elif lvl == 'WARNING':
                            stats['warning_count'] += 1
                            if is_within_24h:
                                stats['warning_count_24h'] += 1
                        elif lvl == 'CRITICAL':
                            stats['critical_count'] += 1
                            if is_within_24h:
                                stats['error_count_24h'] += 1
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"Error reading structured log file: {e}")
    else:
        stats['severity_source'] = 'text'

    stats['timeline'] = [hourly_buckets[k] for k in sorted(hourly_buckets.keys())]

    sec_path = os.path.join(log_dir, 'e_cuzdan_security.log')
    if os.path.exists(sec_path):
        try:
            with open(sec_path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    if line.strip():
                        stats['security_count'] += 1
        except Exception as e:
            logger.error(f"Error reading security log file: {e}")

    err_struct_path = os.path.join(log_dir, 'e_cuzdan_errors_structured.log')
    if os.path.exists(err_struct_path):
        try:
            raw_lines = _tail_lines(err_struct_path, 20)
            for raw_line in reversed(raw_lines):
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                try:
                    import json
                    entry = json.loads(raw_line)
                    lvl = str(entry.get('level', 'ERROR')).upper()
                    if lvl in ('ERROR', 'CRITICAL'):
                        stats['recent_errors'].append({
                            'timestamp': entry.get('timestamp', ''),
                            'level': lvl,
                            'logger': entry.get('logger', entry.get('module', 'uygulama')),
                            'message': entry.get('message', ''),
                        })
                        if len(stats['recent_errors']) >= 5:
                            break
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Error reading structured error log file: {e}")

    if not stats['recent_errors']:
        err_path = os.path.join(log_dir, 'e_cuzdan_errors.log')
        if os.path.exists(err_path):
            try:
                lines = _tail_lines(err_path, 20)
                for line in reversed(lines):
                    line = line.strip()
                    if 'ERROR' in line or 'CRITICAL' in line:
                        stats['recent_errors'].append({
                            'timestamp': line.split(' ')[0] if ' ' in line else '',
                            'level': 'ERROR' if 'ERROR' in line else 'CRITICAL',
                            'logger': 'uygulama',
                            'message': line,
                        })
                        if len(stats['recent_errors']) >= 5:
                            break
            except Exception:
                pass

    return stats


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


def _tail_lines(file_path: str, max_lines: int, *, max_bytes: int = 2 * 1024 * 1024) -> List[str]:
    """Read last N lines of a file safely (bounded memory)."""
    if max_lines <= 0:
        return []
    try:
        with open(file_path, 'rb') as handle:
            handle.seek(0, os.SEEK_END)
            pos = handle.tell()
            if pos <= 0:
                return []

            chunk_size = 8192
            buf = b''
            while pos > 0 and buf.count(b'\n') <= max_lines and len(buf) < max_bytes:
                read_size = min(chunk_size, pos)
                pos -= read_size
                handle.seek(pos)
                buf = handle.read(read_size) + buf

        return buf.decode('utf-8', errors='replace').splitlines()[-max_lines:]
    except OSError:
        return []


def register_monitoring_routes(bp):
    """
    Monitoring route'larını kaydeder
    
    Args:
        bp: Blueprint objesi
    """
    if hasattr(bp, 'before_request') and callable(getattr(bp, 'before_request')):
        @bp.before_request
        def check_monitoring_access():
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))
            from repositories import UserRepository
            user = UserRepository().get_user(session['user_id'])
            if not user:
                flash(i18n.gettext("ui_auto_fd71ebc8847d"), 'error')
                return redirect(url_for('auth.login'))
            if not has_capability(user, Capability.MONITORING_VIEW):
                flash(i18n.gettext("ui_auto_100ea0058791"), 'error')
                return redirect(url_for('dashboard.index'))

    @bp.route('/')
    @login_required
    def monitoring_dashboard():
        """
        Monitoring dashboard sayfası
        """
        logger.debug("Monitoring dashboard accessed")
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
            logger.debug("Monitoring stats API called")
            # Check cache
            cache_key = f"stats_{session.get('user_id')}"
            force_refresh = request.args.get('refresh') in ('true', '1')
            if not force_refresh:
                cached_data = _get_cache_key(cache_key)
                if cached_data:
                    return jsonify(_standard_response(True, data=cached_data))

            stats = _collect_log_stats(_monitoring_log_dir())
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
            - request_id: correlation ID filtresi
            - trace_id: OpenTelemetry trace ID filtresi
        """
        try:
            logger.debug("Monitoring logs API called")
            file_type = request.args.get('file', 'main')
            try:
                line_count = int(request.args.get('lines', 100))
            except ValueError:
                line_count = 100
            line_count = max(1, min(line_count, 1000))
            level_filter = request.args.get('level') or None
            search_term = request.args.get('search') or None
            request_id = request.args.get('request_id') or None
            trace_id = request.args.get('trace_id') or None

            log_file_map = {
                'main': 'e_cuzdan.log',
                'structured': 'e_cuzdan_structured.log',
                'errors': 'e_cuzdan_errors.log',
                'errors_structured': 'e_cuzdan_errors_structured.log',
                'security': 'e_cuzdan_security.log',
                # Backward compatibility (legacy UI/tests)
                'e_cuzdan': 'e_cuzdan.log',
                'e_cuzdan_errors': 'e_cuzdan_errors.log',
                'e_cuzdan_security': 'e_cuzdan_security.log',
            }

            log_file = log_file_map.get(file_type, 'e_cuzdan.log')
            log_dir = _monitoring_log_dir()
            file_path = os.path.join(log_dir, log_file)

            if not os.path.exists(file_path):
                return jsonify({'success': False, 'error': 'Log file not found'}), 404

            structured = is_structured_log_file(log_file)
            try:
                entries = read_log_entries(
                    file_path,
                    structured=structured,
                    line_count=line_count,
                    level=level_filter,
                    search=search_term,
                    request_id=request_id,
                    trace_id=trace_id,
                )
            except Exception as e:
                logger.error(f"Error reading log file: {e}")
                return jsonify(_standard_response(False, error=str(e))), 500

            from utils.log_redaction import redact_message
            for entry in entries:
                entry.message = redact_message(entry.message)

            entry_dicts = [entry.to_dict() for entry in entries]
            raw_logs = [entry.raw for entry in entries]

            return jsonify({
                'success': True,
                'data': {
                    'logs': raw_logs,
                    'entries': entry_dicts,
                    'format': 'json' if structured else 'text',
                    'count': len(entries),
                    'file': file_type,
                }
            })

        except Exception as e:
            logger.error(f"Monitoring logs error: {e}")
            return jsonify(_standard_response(False, error=str(e))), 500

    @bp.route('/api/logs/upload', methods=['POST'])
    @login_required
    def monitoring_log_upload():
        """Log upload endpoint for analysis."""
        file = request.files.get('log_file')
        if not file:
            return jsonify(_standard_response(False, error="No file provided")), 400

        from utils.log_redaction import redact_message
        from utils.log_viewer import parse_log_line
        content = file.read().decode('utf-8', errors='replace')
        entries = []
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            entry = parse_log_line(line, structured=True)
            if entry:
                entry.message = redact_message(entry.message)
                entries.append(entry.to_dict())

        return jsonify(_standard_response(True, data={'entries': entries, 'count': len(entries)}))

    @bp.route('/api/logs/stream', methods=['GET'])
    @login_required
    def monitoring_logs_stream():
        """Bounded Server-Sent Events stream for real-time monitoring."""
        from flask import Response

        from utils.monitoring_stream import monitoring_stream

        channel = monitoring_stream.subscribe()
        if channel is None:
            return jsonify({'error': 'Too many stream subscribers'}), 429
        return Response(
            monitoring_stream.stream(channel),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive',
            }
        )

    @bp.route('/api/logs/timeline', methods=['GET'])
    @bp.route('/api/timeline', methods=['GET'])
    @login_required
    def monitoring_logs_timeline():
        """Hourly ERROR/WARNING counts from structured logs (last 24h)."""
        try:
            stats = _collect_log_stats(_monitoring_log_dir())
            points = stats.get('timeline', [])
            return jsonify(_standard_response(True, data={'points': points}))
        except Exception as e:
            logger.error(f"Monitoring timeline error: {e}")
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
            logger.debug("Monitoring health API called")
            # Check cache
            cache_key = f"health_{session.get('user_id')}"
            force_refresh = request.args.get('refresh') in ('true', '1')
            if not force_refresh:
                cached_data = _get_cache_key(cache_key)
                if cached_data:
                    return jsonify(_standard_response(True, data=cached_data))

            health_status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'components': {
                    'database': 'unknown',
                    'logs': 'unknown',
                    'disk_space': 'unknown',
                    'background_service': 'unknown',
                    'outbox_queue': 'unknown',
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

            # Arka plan servisleri kontrolü
            try:
                from flask import current_app
                from infrastructure.background.background_service import get_background_service_instance
                bg = get_background_service_instance()
                is_running = getattr(bg, 'is_running', False)
                is_testing = bool(current_app and current_app.config.get('TESTING'))
                if is_running or os.getenv('DISABLE_BACKGROUND_SERVICE') == 'true' or is_testing:
                    health_status['components']['background_service'] = 'healthy'
                else:
                    health_status['components']['background_service'] = 'degraded'
            except Exception:
                health_status['components']['background_service'] = 'healthy'

            # Outbox kuyruğu kontrolü
            try:
                from infrastructure.database.outbox_service import count_pending_outbox_messages
                pending_count = count_pending_outbox_messages()
                health_status['components']['outbox_queue'] = 'healthy' if pending_count < 100 else 'warning'
                health_status['outbox_metrics'] = {
                    'pending_count': pending_count,
                    'status': 'healthy' if pending_count < 100 else 'warning',
                }
            except Exception:
                health_status['components']['outbox_queue'] = 'healthy'

            # Önbellek (Cache / Redis) kontrolü
            try:
                from shared.cache import _get_redis_client
                redis_client = _get_redis_client()
                if redis_client:
                    redis_client.ping()
                    health_status['components']['cache'] = 'healthy'
                    health_status['cache_backend'] = 'redis'
                else:
                    health_status['components']['cache'] = 'healthy'
                    health_status['cache_backend'] = 'local'
            except Exception as cache_err:
                health_status['components']['cache'] = 'warning'
                health_status['issues'].append(f'Cache ping failed: {cache_err}')

            # Cache the result
            _set_cache(cache_key, health_status)

            return jsonify(_standard_response(True, data=health_status))

        except Exception as e:
            logger.error(f"Monitoring health error: {e}")
            return jsonify(_standard_response(False, error=str(e))), 500

    @bp.route('/api/summary', methods=['GET'])
    @login_required
    def monitoring_summary():
        """
        Konsolide monitoring özet bilgileri
        
        Tek endpoint ile tüm özet bilgileri getir:
        - Health status
        - Log statistics
        - Recent errors
        - System metrics
        
        Returns:
            JSON response with consolidated monitoring summary
        """
        try:
            logger.debug("Monitoring summary API called")
            # Check cache
            cache_key = f"summary_{session.get('user_id')}"
            force_refresh = request.args.get('refresh') in ('true', '1')
            if not force_refresh:
                cached_data = _get_cache_key(cache_key)
                if cached_data:
                    return jsonify(_standard_response(True, data=cached_data))

            # Get health status
            health_response = monitoring_health()
            health_data = health_response.get_json()

            # Get stats
            stats_response = monitoring_stats()
            stats_data = stats_response.get_json()

            # Build consolidated summary
            summary = {
                'health': health_data.get('data') if health_data.get('success') else None,
                'stats': stats_data.get('data') if stats_data.get('success') else None,
                'timestamp': datetime.now().isoformat(),
                'quick_metrics': {
                    'system_status': health_data.get('data', {}).get('status', 'unknown') if health_data.get('success') else 'unknown',
                    'error_count_24h': stats_data.get('data', {}).get('error_count_24h', 0) if stats_data.get('success') else 0,
                    'warning_count_24h': stats_data.get('data', {}).get('warning_count_24h', 0) if stats_data.get('success') else 0,
                    'disk_free_percent': health_data.get('data', {}).get('disk_usage', {}).get('free_percent', 0) if health_data.get('success') else 0,
                    'uptime_hours': 24  # Placeholder - could be calculated from app start time
                }
            }

            # Cache the result (shorter TTL for summary)
            _cache_ttl['summary'] = 15  # 15 seconds
            _set_cache(cache_key, summary)

            return jsonify(_standard_response(True, data=summary))

        except Exception as e:
            logger.error(f"Monitoring summary error: {e}")
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

            from repositories import MonitoringRepository
            monitoring_repo = MonitoringRepository()
            user_id = session.get('user_id')
            tenant_id = session.get('tenant_id')

            if request.method == 'GET':
                config = monitoring_repo.get_alert_config(user_id=user_id, tenant_id=tenant_id)

                if not config:
                    # Varsayılan konfigürasyon döndür
                    default_config = {
                        'email_alerts_enabled': False,
                        'smtp_server': None,
                        'smtp_port': None,
                        'smtp_username': None,
                        'from_email': None,
                        'to_emails': [],
                        'alert_thresholds': {
                            'error_rate': 10,  # errors per minute
                            'critical_rate': 1,  # critical per minute
                            'disk_space_percent': 10
                        }
                    }
                    return jsonify(_standard_response(True, data=default_config))

                # Mevcut konfigürasyonu döndür
                config_data = {
                    'email_alerts_enabled': config.email_alerts_enabled,
                    'smtp_server': config.smtp_server,
                    'smtp_port': config.smtp_port,
                    'smtp_username': config.smtp_username,
                    'from_email': config.from_email,
                    'to_emails': config.to_emails or [],
                    'alert_thresholds': config.alert_thresholds or {
                        'error_rate': 10,
                        'critical_rate': 1,
                        'disk_space_percent': 10
                    }
                }
                return jsonify(_standard_response(True, data=config_data))

            elif request.method == 'POST':
                data = request.get_json() or {}
                monitoring_repo.save_alert_config(user_id=user_id, tenant_id=tenant_id, data=data)
                return jsonify(_standard_response(True, data={'message': 'Configuration updated'}))

        except Exception as e:
            logger.error(f"Monitoring alerts config error: {e}")
            return jsonify(_standard_response(False, error=str(e))), 500

    @bp.route('/api/alerts/status', methods=['GET'])
    @login_required
    def monitoring_alerts_status():
        """Return current log alert evaluation status."""
        try:
            from utils.log_alert_monitor import get_log_alert_monitor

            status = get_log_alert_monitor().evaluate()
            return jsonify(_standard_response(True, data=status))
        except Exception as e:
            logger.error(f"Monitoring alerts status error: {e}")
            return jsonify(_standard_response(False, error=str(e))), 500

    @bp.route('/api/logs/archive', methods=['POST'])
    @login_required
    def monitoring_logs_archive():
        """Log dosyalarını güvenle arşivle ve alan aç."""
        try:
            import zipfile

            log_dir = _monitoring_log_dir()
            archive_dir = os.path.join(log_dir, 'archive')
            os.makedirs(archive_dir, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            zip_filename = f'log_archive_{timestamp}.zip'
            zip_path = os.path.join(archive_dir, zip_filename)

            target_files = [
                'e_cuzdan.log',
                'e_cuzdan_errors.log',
                'e_cuzdan_errors_structured.log',
                'e_cuzdan_structured.log',
            ]

            archived = []
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for f in target_files:
                    p = os.path.join(log_dir, f)
                    if os.path.exists(p) and os.path.getsize(p) > 0:
                        zipf.write(p, arcname=f)
                        archived.append(f)
                        try:
                            with open(p, 'w', encoding='utf-8'):
                                pass
                        except Exception:
                            pass

            _clear_cache()
            return jsonify(_standard_response(True, data={
                'message': 'Loglar başarıyla arşivlendi ve aktif dosyalar sıfırlandı.',
                'archive_file': zip_filename,
                'archived_count': len(archived),
                'files': archived
            }))
        except Exception as e:
            logger.error(f"Log archiving error: {e}")
            return jsonify(_standard_response(False, error=str(e))), 500


# Blueprint kayıt fonksiyonu
def register_monitoring_routes_bp():
    """Monitoring blueprint'ini döndür"""
    return monitoring_bp
