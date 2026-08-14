"""Log file parsing helpers for the monitoring dashboard."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List, Optional


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

    return LogEntry(
        timestamp=str(data.get('timestamp', '')),
        level=str(data.get('level', 'INFO')),
        message=str(data.get('message', '')),
        raw=line,
        logger=data.get('logger'),
        request_id=request_id,
        trace_id=trace_id,
        span_id=data.get('span_id'),
        module=data.get('module'),
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


def filter_log_entries(
    entries: Iterable[LogEntry],
    *,
    level: Optional[str] = None,
    search: Optional[str] = None,
    request_id: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> List[LogEntry]:
    result: List[LogEntry] = []
    search_lower = search.lower() if search else None

    for entry in entries:
        if level and entry.level != level:
            continue
        if request_id and (not entry.request_id or request_id not in entry.request_id):
            if request_id not in entry.raw:
                continue
        if trace_id and (not entry.trace_id or trace_id not in entry.trace_id):
            if trace_id not in entry.raw:
                continue
        if search_lower:
            haystack = ' '.join(
                filter(None, [entry.message, entry.logger, entry.raw, entry.request_id, entry.trace_id])
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
) -> List[LogEntry]:
    lines = _tail_lines(file_path, line_count * 5)

    entries: List[LogEntry] = []
    for line in lines:
        parsed = parse_log_line(line, structured=structured)
        if parsed:
            entries.append(parsed)

    filtered = filter_log_entries(
        entries,
        level=level,
        search=search,
        request_id=request_id,
        trace_id=trace_id,
    )
    return filtered[-line_count:]


def _tail_lines(file_path: str, max_lines: int, *, max_bytes: int = 2 * 1024 * 1024) -> List[str]:
    """Return last N lines from a file without reading the whole file.

    - Bounded by `max_bytes` to avoid memory spikes on huge logs.
    - Best-effort: returns fewer lines if file is smaller or unreadable.
    """
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

            # Read backwards until we have enough newlines or hit bounds.
            while pos > 0 and buf.count(b'\n') <= max_lines and len(buf) < max_bytes:
                read_size = min(chunk_size, pos)
                pos -= read_size
                handle.seek(pos)
                buf = handle.read(read_size) + buf

        # Decode once (replace invalid bytes) and split.
        text = buf.decode('utf-8', errors='replace')
        lines = text.splitlines()
        return lines[-max_lines:]
    except OSError:
        return []
