"""Test special code service."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from domain.users.services.special_code_service import get_special_code_service

# Test the special code service
service = get_special_code_service()

# Test code validation
result = service.validate_code('emincetin10', 1, 'test_tenant')
print(f"Validation result: {result}")

# Test code info
info = service.get_code_info('emincetin10')
print(f"Code info: {info}")

# List all codes
codes = service.list_available_codes()
print(f"All codes: {codes}")
