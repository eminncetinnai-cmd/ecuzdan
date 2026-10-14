"""Unit tests for log viewer parsing."""

import json

import pytest

from utils.log_viewer import (
    LogEntry,
    filter_log_entries,
    is_structured_log_file,
    parse_log_line,
)


@pytest.mark.unit
def test_is_structured_log_file():
    assert is_structured_log_file('e_cuzdan_structured.log') is True
    assert is_structured_log_file('e_cuzdan.log') is False


@pytest.mark.unit
def test_parse_text_line_with_request_id():
    line = (
        '2026-08-14 11:48:16 [abcd1234' + '0' * 24 + '] [req-abc123] '
        'ERROR [routes.auth] Login failed'
    )
    entry = parse_log_line(line)
    assert entry.level == 'ERROR'
    assert entry.request_id == 'req-abc123'
    assert entry.message == 'Login failed'


@pytest.mark.unit
def test_parse_json_line():
    payload = {
        'timestamp': '2026-08-14T08:00:00.000000Z',
        'level': 'WARNING',
        'message': 'Slow query',
        'request_id': 'abc123',
        'trace_id': 'deadbeef' + '0' * 24,
    }
    entry = parse_log_line(json.dumps(payload), structured=True)
    assert entry.level == 'WARNING'
    assert entry.request_id == 'abc123'
    assert entry.trace_id.startswith('deadbeef')


@pytest.mark.unit
def test_filter_by_trace_id():
    entries = [
        LogEntry('', 'ERROR', 'one', 'raw1', trace_id='abc123def456'),
        LogEntry('', 'INFO', 'two', 'raw2', trace_id='zzz'),
    ]
    filtered = filter_log_entries(entries, trace_id='abc123')
    assert len(filtered) == 1
    assert filtered[0].message == 'one'


@pytest.mark.unit
def test_parse_json_preserves_non_standard_fields():
    payload = {
        'timestamp': '2026-08-14T08:00:00Z',
        'level': 'error',
        'message': 'Backup failed',
        'logger': 'backup',
        'exception': {'type': 'ValueError'},
        'tenant_id': 'tenant-a',
    }
    entry = parse_log_line(json.dumps(payload), structured=True)
    assert entry.level == 'ERROR'
    assert entry.fields == {'exception': {'type': 'ValueError'}, 'tenant_id': 'tenant-a'}


@pytest.mark.unit
def test_read_log_entries_finds_matches_before_unfiltered_tail(tmp_path):
    from utils.log_viewer import read_log_entries

    path = tmp_path / 'e_cuzdan_structured.log'
    lines = [
        json.dumps({'timestamp': '2026-08-14T08:00:00Z', 'level': 'ERROR', 'message': 'target failure'}),
        *[
            json.dumps({'timestamp': f'2026-08-14T08:00:{index:02d}Z', 'level': 'INFO', 'message': 'noise'})
            for index in range(1, 40)
        ],
    ]
    path.write_text('\n'.join(lines), encoding='utf-8')

    entries = read_log_entries(str(path), structured=True, line_count=5, level='ERROR')

    assert len(entries) == 1
    assert entries[0].message == 'target failure'


@pytest.mark.unit
def test_filter_by_since_timestamp():
    entries = [
        LogEntry('2026-08-19T08:00:00+00:00', 'ERROR', 'old', 'old'),
        LogEntry('2026-08-19T10:00:00+00:00', 'ERROR', 'new', 'new'),
    ]
    filtered = filter_log_entries(entries, since='2026-08-19T09:00:00+00:00')
    assert [entry.message for entry in filtered] == ['new']
