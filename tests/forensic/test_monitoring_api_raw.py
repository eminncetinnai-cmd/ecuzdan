"""
Forensic Test - Raw API Response Analysis
Monitoring API'nin gerçek response'unu incelemek için test
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

os.environ['DISABLE_BACKGROUND_SERVICE'] = 'true'

import json


@pytest.mark.forensic
def test_monitoring_api_raw_response(privileged_authenticated_client):
    """Monitoring API'nin ham response'unu incele - authenticated client ile"""

    print("=" * 80)
    print("FORENSIC API RESPONSE ANALYSIS")
    print("=" * 80)

    # Test 1: /monitoring/api/logs raw response
    print("\n[TEST 1] GET /monitoring/api/logs?file=e_cuzdan&lines=5")
    print("-" * 80)
    response = privileged_authenticated_client.get('/monitoring/api/logs?file=e_cuzdan&lines=5')

    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.content_type}")
    print(f"Response Size: {len(response.data)} bytes")
    print(f"Headers: {dict(response.headers)}")

    try:
        data = json.loads(response.data)
        print("\nJSON Structure:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        # Structure analysis
        print("\nStructure Analysis:")
        print(f"  - Has 'success' key: {'success' in data}")
        print(f"  - Has 'data' key: {'data' in data}")
        print(f"  - Has 'error' key: {'error' in data}")

        if 'data' in data:
            print(f"  - Data type: {type(data['data'])}")
            print(f"  - Data keys: {data['data'].keys() if isinstance(data['data'], dict) else 'N/A'}")

            if isinstance(data['data'], dict) and 'logs' in data['data']:
                logs = data['data']['logs']
                print(f"  - Logs count: {len(logs)}")
                if logs:
                    print(f"  - First log: {logs[0][:100]}...")
                    print(f"  - Last log: {logs[-1][:100]}...")
    except json.JSONDecodeError as e:
        print(f"\nJSON Decode Error: {e}")
        print("Raw Response (first 500 chars):")
        print(response.data[:500].decode('utf-8', errors='replace'))

    # Test 2: /monitoring/api/stats raw response
    print("\n" + "=" * 80)
    print("[TEST 2] GET /monitoring/api/stats")
    print("-" * 80)
    response = privileged_authenticated_client.get('/monitoring/api/stats')

    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.content_type}")

    try:
        data = json.loads(response.data)
        print("\nJSON Structure:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except json.JSONDecodeError as e:
        print(f"\nJSON Decode Error: {e}")

    # Test 3: /monitoring/api/health raw response
    print("\n" + "=" * 80)
    print("[TEST 3] GET /monitoring/api/health")
    print("-" * 80)
    response = privileged_authenticated_client.get('/monitoring/api/health')

    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.content_type}")

    try:
        data = json.loads(response.data)
        print("\nJSON Structure:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except json.JSONDecodeError as e:
        print(f"\nJSON Decode Error: {e}")

    # Test 4: Test marker search
    print("\n" + "=" * 80)
    print("[TEST 4] Search for forensic test marker")
    print("-" * 80)
    response = privileged_authenticated_client.get('/monitoring/api/logs?file=e_cuzdan&lines=100&search=MONITORING_FORENSIC_TEST_MARKER')

    print(f"Status Code: {response.status_code}")

    try:
        data = json.loads(response.data)
        if 'data' in data and 'logs' in data['data']:
            logs = data['data']['logs']
            print(f"Logs found with marker: {len(logs)}")
            if logs:
                for log in logs:
                    print(f"  - {log}")
        else:
            print(f"Response structure: {data.keys()}")
    except json.JSONDecodeError as e:
        print(f"\nJSON Decode Error: {e}")

    print("\n" + "=" * 80)
    print("FORENSIC ANALYSIS COMPLETE")
    print("=" * 80)
