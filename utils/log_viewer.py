"""Log file parsing helpers for the monitoring dashboard."""

from __future__ import annotations

import json
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

STRUCTURED_LOG_SUFFIX = '_structured.log'


@dataclass
class LogEntry:
    timestamp: str
    level: str
    message: str
    raw: str
    logger: Optional[str] = None
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    module: Optional[str] = None
    fields: Dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def is_structured_log_file(filename: str) -> bool:
    return filename.endswith('.log') and 'structured' in filename


def parse_log_line(line: str, structured: bool = False) -> Optional[LogEntry]:
    line = line.rstrip('\n')
    if not line.strip():
        return None

    if structured or line.lstrip().startswith('{'):
        return _parse_json_line(line)
    return _parse_text_line(line)


def _parse_json_line(line: str) -> Optional[LogEntry]:
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return _parse_text_line(line)

    trace_id = data.get('trace_id')
    if trace_id and trace_id == '0' * 32:
        trace_id = None

    request_id = data.get('request_id')
    if request_id in (None, '-', ''):
        request_id = None

    known_fields = {
        'timestamp', 'level', 'message', 'logger', 'request_id',
        'trace_id', 'span_id', 'module',
    }
    fields = {key: value for key, value in data.items() if key not in known_fields}

    return LogEntry(
        timestamp=str(data.get('timestamp', '')),
        level=str(data.get('level', 'INFO')).upper(),
        message=str(data.get('message', '')),
        raw=line,
        logger=data.get('logger'),
        request_id=request_id,
        trace_id=trace_id,
        span_id=data.get('span_id'),
        module=data.get('module'),
        fields=fields,
    )


def _parse_text_line(line: str) -> Optional[LogEntry]:
    # Format: 2026-08-14 11:48:16 [trace] [request_id] LEVEL [logger] message
    import re

    match = re.match(
        r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+\[([0-9a-f]{32})\]\s+\[([^\]]*)\]\s+'
        r'(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s+\[([^\]]+)\]\s+(.*)$',
        line,
    )
    if match:
        trace_id = match.group(2)
        request_id = match.group(3)
        return LogEntry(
            timestamp=match.group(1),
            level=match.group(4),
            message=match.group(6),
            raw=line,
            logger=match.group(5),
            request_id=request_id if request_id not in ('', '-') else None,
            trace_id=trace_id if trace_id != '0' * 32 else None,
        )

    # Legacy format without request_id
    match = re.match(
        r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+\[([0-9a-f]{32})\]\s+'
        r'(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s+\[([^\]]+)\]\s+(.*)$',
        line,
    )
    if match:
        trace_id = match.group(2)
        return LogEntry(
            timestamp=match.group(1),
            level=match.group(3),
            message=match.group(5),
            raw=line,
            logger=match.group(4),
            trace_id=trace_id if trace_id != '0' * 32 else None,
        )

    level = 'INFO'
    for candidate in ('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'):
        if candidate in line:
            level = candidate
            break

    return LogEntry(
        timestamp='',
        level=level,
        message=line,
        raw=line,
    )


def iter_log_entries(file_path: str, *, structured: bool) -> Iterator[LogEntry]:
    """Yield parsed entries from a log file with bounded per-entry memory."""
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return

    try:
        with path.open('r', encoding='utf-8', errors='replace') as handle:
            for line in handle:
                parsed = parse_log_line(line, structured=structured)
                if parsed:
                    yield parsed
    except OSError:
        return


def _parse_timestamp(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def filter_log_entries(
    entries: Iterable[LogEntry],
    *,
    level: Optional[str] = None,
    search: Optional[str] = None,
    request_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    since: Optional[str] = None,
) -> List[LogEntry]:
    result: List[LogEntry] = []
    normalized_level = level.upper() if level else None
    search_lower = search.lower() if search else None
    since_timestamp = _parse_timestamp(since) if since else None

    for entry in entries:
        if normalized_level and entry.level.upper() != normalized_level:
            continue
        if since:
            entry_timestamp = _parse_timestamp(entry.timestamp)
            if not since_timestamp or not entry_timestamp or entry_timestamp < since_timestamp:
                continue
        if request_id and (not entry.request_id or request_id not in entry.request_id):
            if request_id not in entry.raw:
                continue
        if trace_id and (not entry.trace_id or trace_id not in entry.trace_id):
            if trace_id not in entry.raw:
                continue
        if search_lower:
            field_values = [str(value) for value in entry.fields.values()]
            haystack = ' '.join(
                filter(
                    None,
                    [
                        entry.message,
                        entry.logger,
                        entry.raw,
                        entry.request_id,
                        entry.trace_id,
                        entry.module,
                        *field_values,
                    ],
                )
            ).lower()
            if search_lower not in haystack:
                continue
        result.append(entry)

    return result


def read_log_entries(
    file_path: str,
    *,
    structured: bool,
    line_count: int = 100,
    level: Optional[str] = None,
    search: Optional[str] = None,
    request_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    since: Optional[str] = None,
) -> List[LogEntry]:
    """Read the latest matching entries without losing matches before the raw tail.

    The old implementation only parsed ``line_count * 5`` physical lines and
    filtered afterwards. A selective ERROR/request-id query could therefore
    return an empty result even when a matching entry existed earlier in a
    large file. This implementation scans incrementally and keeps only the
    requested number of matches in memory.
    """
    if line_count <= 0:
        return []

    matched: deque[LogEntry] = deque(maxlen=line_count)
    for entry in iter_log_entries(file_path, structured=structured):
        if filter_log_entries(
            [entry],
            level=level,
            search=search,
            request_id=request_id,
            trace_id=trace_id,
            since=since,
        ):
            matched.append(entry)
    return list(matched)


def _tail_lines(file_path: str, max_lines: int, *, max_bytes: int = 2 * 1024 * 1024) -> List[str]:
    """Return last N lines from a log file without reading the whole file."""
    if max_lines <= 0:
        return []

    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return []

    try:
        with path.open('rb') as handle:
            handle.seek(0, 2)
            file_size = handle.tell()
            if file_size <= 0:
                return []

            chunk_size = 8192
            pos = file_size
            buf = b''

            while pos > 0 and buf.count(b'\n') <= max_lines and len(buf) < max_bytes:
                read_size = min(chunk_size, pos)
                pos -= read_size
                handle.seek(pos)
                buf = handle.read(read_size) + buf

        text = buf.decode('utf-8', errors='replace')
        return text.splitlines()[-max_lines:]
    except OSError:
        return []
