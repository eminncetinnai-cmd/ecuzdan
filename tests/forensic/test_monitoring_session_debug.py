"""
Forensic Test - Session Debugging
Monitoring API'lerinin session cookie ile çalışıp çalışmadığını test et
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

os.environ['DISABLE_BACKGROUND_SERVICE'] = 'true'


@pytest.mark.forensic
def test_monitoring_session_cookie(privileged_authenticated_client):
    """Session cookie ile API çağrısının çalıştığını test et"""

    print("=" * 80)
    print("SESSION COOKIE DEBUG TEST")
    print("=" * 80)

    # Test 1: Health API with session
    print("\n[TEST 1] GET /monitoring/api/health with authenticated session")
    print("-" * 80)
    response = privileged_authenticated_client.get('/monitoring/api/health')

    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.content_type}")
    print(f"Set-Cookie headers: {response.headers.getlist('Set-Cookie')}")

    if response.status_code == 200:
        import json
        data = json.loads(response.data)
        print(f"Response data keys: {data.keys()}")
        print(f"Success: {data.get('success')}")
        if 'data' in data:
            print(f"Data keys: {data['data'].keys()}")
    else:
        print(f"Response body: {response.data[:500]}")

    # Test 2: Stats API with session
    print("\n[TEST 2] GET /monitoring/api/stats with authenticated session")
    print("-" * 80)
    response = privileged_authenticated_client.get('/monitoring/api/stats')

    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.content_type}")

    if response.status_code == 200:
        import json
        data = json.loads(response.data)
        print(f"Response data keys: {data.keys()}")
        print(f"Success: {data.get('success')}")
    else:
        print(f"Response body: {response.data[:500]}")

    # Test 3: Logs API with session
    print("\n[TEST 3] GET /monitoring/api/logs with authenticated session")
    print("-" * 80)
    response = privileged_authenticated_client.get('/monitoring/api/logs?file=e_cuzdan&lines=5')

    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.content_type}")

    if response.status_code == 200:
        import json
        data = json.loads(response.data)
        print(f"Response data keys: {data.keys()}")
        print(f"Success: {data.get('success')}")
        if 'data' in data and 'logs' in data['data']:
            print(f"Logs count: {len(data['data']['logs'])}")
    else:
        print(f"Response body: {response.data[:500]}")

    print("\n" + "=" * 80)
    print("SESSION COOKIE DEBUG COMPLETE")
    print("=" * 80)
