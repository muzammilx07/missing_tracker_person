#!/usr/bin/env python3
"""
QA Testing Suite for Missing Person Tracker
Comprehensive test coverage for backend APIs, auth flows, and error cases.

Test Stages:
1. Backend Health Check
2. Auth APIs (register, login)
3. Protected APIs (with token)
4. Public APIs (without auth)
5. Case Filing Flow
6. Admin Flow
7. Error Cases & Edge Cases
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import sys

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 5

# Test Data
TEST_USER_EMAIL = f"qa_test_{int(time.time())}@example.com"
TEST_USER_NAME = "QA Test User"
TEST_USER_PHONE = "9876543210"
TEST_USER_PASSWORD = "TestPass123!"

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

# Test Results
passed_tests = []
failed_tests = []
test_data = {}

def print_header(text):
    print(f"\n{BLUE}{BOLD}{'='*60}")
    print(f"{text.center(60)}")
    print(f"{'='*60}{RESET}\n")

def print_test(test_name: str, result: bool, details: str = ""):
    status = f"{GREEN}✓ PASS{RESET}" if result else f"{RED}✗ FAIL{RESET}"
    print(f"{status} | {test_name}")
    if details:
        print(f"      {details}")
    return result

def test_result(test_name: str, result: bool, details: str = ""):
    if result:
        passed_tests.append(test_name)
    else:
        failed_tests.append(test_name)
    print_test(test_name, result, details)

# ============================================================================
# STEP 1: BACKEND HEALTH CHECK
# ============================================================================
def test_backend_health():
    print_header("STEP 1: Backend Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
        result = response.status_code == 200
        test_result(
            "Backend server is running",
            result,
            f"Status: {response.status_code}"
        )
        return result
    except requests.exceptions.ConnectionError:
        test_result(
            "Backend server is running",
            False,
            f"Cannot connect to {BASE_URL}"
        )
        return False
    except Exception as e:
        test_result(
            "Backend server is running",
            False,
            str(e)
        )
        return False

# ============================================================================
# STEP 2: AUTH APIs
# ============================================================================
def test_auth_apis():
    print_header("STEP 2: Auth APIs (Register & Login)")
    
    all_passed = True
    
    # Test 2.1: Register new user
    print(f"\n{BOLD}Test 2.1: User Registration{RESET}")
    try:
        payload = {
            "first_name": TEST_USER_NAME.split()[0],
            "last_name": TEST_USER_NAME.split()[1],
            "email": TEST_USER_EMAIL,
            "phone": TEST_USER_PHONE,
            "password": TEST_USER_PASSWORD
        }
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json=payload,
            timeout=TIMEOUT
        )
        result = response.status_code == 201
        test_result(
            "POST /auth/register - User registration",
            result,
            f"Status: {response.status_code}"
        )
        if not result:
            print(f"      Response: {response.text[:100]}")
        all_passed = all_passed and result
    except Exception as e:
        test_result("POST /auth/register - User registration", False, str(e))
        all_passed = False
    
    # Test 2.2: Login user
    print(f"\n{BOLD}Test 2.2: User Login{RESET}")
    try:
        payload = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=payload,
            timeout=TIMEOUT
        )
        result = response.status_code == 200
        test_result(
            "POST /auth/login - Get auth token",
            result,
            f"Status: {response.status_code}"
        )
        
        if result:
            data = response.json()
            token = data.get("access_token")
            user_role = data.get("role")
            test_data["token"] = token
            test_data["user_id"] = data.get("user_id")
            test_data["user_email"] = TEST_USER_EMAIL
            
            token_received = bool(token)
            test_result(
                "POST /auth/login - Token received",
                token_received,
                f"Token: {token[:20]}..." if token else "No token"
            )
            all_passed = all_passed and token_received
        else:
            print(f"      Response: {response.text[:100]}")
            all_passed = False
    except Exception as e:
        test_result("POST /auth/login - Get auth token", False, str(e))
        all_passed = False
    
    # Test 2.3: Invalid credentials
    print(f"\n{BOLD}Test 2.3: Error Case - Invalid Credentials{RESET}")
    try:
        payload = {
            "email": TEST_USER_EMAIL,
            "password": "WrongPassword123"
        }
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=payload,
            timeout=TIMEOUT
        )
        result = response.status_code in [401, 400]  # Unauthorized or Bad Request
        test_result(
            "POST /auth/login - Invalid credentials return error",
            result,
            f"Status: {response.status_code} (expected 401 or 400)"
        )
        all_passed = all_passed and result
    except Exception as e:
        test_result(
            "POST /auth/login - Invalid credentials return error",
            False,
            str(e)
        )
        all_passed = False
    
    return all_passed

# ============================================================================
# STEP 3: PROTECTED APIs
# ============================================================================
def test_protected_apis():
    print_header("STEP 3: Protected API (with Token)")
    
    if "token" not in test_data:
        print(f"{RED}Skipping - No token available{RESET}")
        return False
    
    all_passed = True
    token = test_data["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 3.1: Get user cases
    print(f"\n{BOLD}Test 3.1: Get Protected Resource{RESET}")
    try:
        response = requests.get(
            f"{BASE_URL}/cases/my-cases",
            headers=headers,
            timeout=TIMEOUT
        )
        result = response.status_code == 200
        test_result(
            "GET /cases/my-cases - Protected endpoint with token",
            result,
            f"Status: {response.status_code}"
        )
        if result:
            data = response.json()
            print(f"      Cases found: {len(data) if isinstance(data, list) else 0}")
        all_passed = all_passed and result
    except Exception as e:
        test_result(
            "GET /cases/my-cases - Protected endpoint with token",
            False,
            str(e)
        )
        all_passed = False
    
    # Test 3.2: Missing token (401 error)
    print(f"\n{BOLD}Test 3.2: Error Case - Missing Token{RESET}")
    try:
        response = requests.get(
            f"{BASE_URL}/cases/my-cases",
            timeout=TIMEOUT
        )
        result = response.status_code == 401
        test_result(
            "GET /cases/my-cases - No token returns 401",
            result,
            f"Status: {response.status_code} (expected 401)"
        )
        all_passed = all_passed and result
    except Exception as e:
        test_result(
            "GET /cases/my-cases - No token returns 401",
            False,
            str(e)
        )
        all_passed = False
    
    # Test 3.3: Invalid token (401 error)
    print(f"\n{BOLD}Test 3.3: Error Case - Invalid Token{RESET}")
    try:
        bad_headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = requests.get(
            f"{BASE_URL}/cases/my-cases",
            headers=bad_headers,
            timeout=TIMEOUT
        )
        result = response.status_code == 401
        test_result(
            "GET /cases/my-cases - Invalid token returns 401",
            result,
            f"Status: {response.status_code} (expected 401)"
        )
        all_passed = all_passed and result
    except Exception as e:
        test_result(
            "GET /cases/my-cases - Invalid token returns 401",
            False,
            str(e)
        )
        all_passed = False
    
    return all_passed

# ============================================================================
# STEP 4: PUBLIC APIs
# ============================================================================
def test_public_apis():
    print_header("STEP 4: Public APIs (No Auth Required)")
    
    all_passed = True
    
    # Test 4.1: Submit sighting without auth
    print(f"\n{BOLD}Test 4.1: Submit Public Sighting{RESET}")
    try:
        # First, create a test image or use a simple file
        import base64
        import io
        from PIL import Image
        
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        files = {'photo': ('test.png', img_bytes, 'image/png')}
        data = {
            'sighting_latitude': '19.0760',
            'sighting_longitude': '72.8777',
            'sighting_city': 'Mumbai',
            'sighting_state': 'Maharashtra',
            'sighting_date': datetime.now().isoformat(),
            'name': 'Test Reporter',
            'phone': '9876543210'
        }
        
        response = requests.post(
            f"{BASE_URL}/sightings",
            files=files,
            data=data,
            timeout=TIMEOUT
        )
        result = response.status_code in [200, 201]
        test_result(
            "POST /sightings - Public sighting submission",
            result,
            f"Status: {response.status_code}"
        )
        if result:
            test_data["sighting_id"] = response.json().get("id")
        all_passed = all_passed and result
    except Exception as e:
        test_result(
            "POST /sightings - Public sighting submission",
            False,
            str(e)
        )
        all_passed = False
    
    # Test 4.2: Missing required fields
    print(f"\n{BOLD}Test 4.2: Error Case - Missing Required Fields{RESET}")
    try:
        # Submit sighting without photo (required)
        data = {
            'sighting_latitude': '19.0760',
            'sighting_longitude': '72.8777',
            'sighting_city': 'Mumbai'
        }
        response = requests.post(
            f"{BASE_URL}/sightings",
            data=data,
            timeout=TIMEOUT
        )
        result = response.status_code in [400, 422]  # Bad Request or Unprocessable Entity
        test_result(
            "POST /sightings - Missing required photo returns error",
            result,
            f"Status: {response.status_code} (expected 400/422)"
        )
        all_passed = all_passed and result
    except Exception as e:
        test_result(
            "POST /sightings - Missing required photo returns error",
            False,
            str(e)
        )
        all_passed = False
    
    return all_passed

# ============================================================================
# STEP 5: CASE FILING FLOW
# ============================================================================
def test_case_filing_flow():
    print_header("STEP 5: Case Filing Flow (End-to-End)")
    
    if "token" not in test_data:
        print(f"{RED}Skipping - No token available{RESET}")
        return False
    
    all_passed = True
    token = test_data["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 5.1: Create case
    print(f"\n{BOLD}Test 5.1: File Missing Person Case{RESET}")
    try:
        payload = {
            "first_name": "John",
            "last_name": "Doe",
            "age": 25,
            "gender": "male",
            "last_seen_date": (datetime.now() - timedelta(days=3)).isoformat(),
            "last_seen_city": "Mumbai",
            "last_seen_state": "Maharashtra",
            "description": "QA Test Case - Missing person report",
            "photo_url": "https://via.placeholder.com/300",
            "auto_dispatch_enabled": False,
            "family_emails": []
        }
        response = requests.post(
            f"{BASE_URL}/cases",
            json=payload,
            headers=headers,
            timeout=TIMEOUT
        )
        result = response.status_code in [200, 201]
        test_result(
            "POST /cases - File new case",
            result,
            f"Status: {response.status_code}"
        )
        if result:
            data = response.json()
            test_data["case_id"] = data.get("id")
            test_data["case_number"] = data.get("case_number")
            print(f"      Case ID: {test_data['case_id']}, Case #: {test_data['case_number']}")
        else:
            print(f"      Response: {response.text[:200]}")
        all_passed = all_passed and result
    except Exception as e:
        test_result(
            "POST /cases - File new case",
            False,
            str(e)
        )
        all_passed = False
    
    # Test 5.2: Get case detail
    if "case_id" in test_data:
        print(f"\n{BOLD}Test 5.2: Retrieve Case Detail{RESET}")
        try:
            response = requests.get(
                f"{BASE_URL}/cases/{test_data['case_id']}",
                headers=headers,
                timeout=TIMEOUT
            )
            result = response.status_code == 200
            test_result(
                "GET /cases/{id} - Get case detail",
                result,
                f"Status: {response.status_code}"
            )
            if result:
                data = response.json()
                print(f"      Status: {data.get('status')}, Matches: {data.get('match_count', 0)}")
            all_passed = all_passed and result
        except Exception as e:
            test_result(
                "GET /cases/{id} - Get case detail",
                False,
                str(e)
            )
            all_passed = False
    
    # Test 5.3: Verify case status
    if "case_id" in test_data:
        print(f"\n{BOLD}Test 5.3: Verify Case Status{RESET}")
        try:
            response = requests.get(
                f"{BASE_URL}/cases/{test_data['case_id']}",
                headers=headers,
                timeout=TIMEOUT
            )
            if response.status_code == 200:
                status = response.json().get("status")
                result = status in ["open", "pending", "draft"]
                test_result(
                    "GET /cases/{id} - Case has valid status",
                    result,
                    f"Status: {status}"
                )
                all_passed = all_passed and result
            else:
                all_passed = False
        except Exception as e:
            all_passed = False
    
    return all_passed

# ============================================================================
# STEP 6: ADMIN FLOW
# ============================================================================
def test_admin_flow():
    print_header("STEP 6: Admin Flow & Endpoints")
    
    if "token" not in test_data:
        print(f"{RED}Skipping - No token available{RESET}")
        return False
    
    all_passed = True
    token = test_data["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 6.1: Admin dashboard stats
    print(f"\n{BOLD}Test 6.1: Admin Dashboard Stats{RESET}")
    try:
        response = requests.get(
            f"{BASE_URL}/admin/stats",
            headers=headers,
            timeout=TIMEOUT
        )
        # Note: May return 403 if user is not admin
        result = response.status_code in [200, 403]
        if response.status_code == 403:
            test_result(
                "GET /admin/stats - Admin endpoint (user not admin)",
                True,
                "Status: 403 Forbidden (expected for non-admin user)"
            )
        else:
            result = response.status_code == 200
            test_result(
                "GET /admin/stats - Admin endpoint accessible",
                result,
                f"Status: {response.status_code}"
            )
        all_passed = all_passed and result
    except Exception as e:
        test_result(
            "GET /admin/stats - Admin endpoint",
            False,
            str(e)
        )
        all_passed = False
    
    # Test 6.2: Get pending matches (if any)
    print(f"\n{BOLD}Test 6.2: Pending Matches Endpoint{RESET}")
    try:
        response = requests.get(
            f"{BASE_URL}/matches/pending",
            headers=headers,
            timeout=TIMEOUT
        )
        result = response.status_code in [200, 403]
        test_result(
            "GET /matches/pending - Retrieve pending matches",
            result,
            f"Status: {response.status_code}"
        )
        all_passed = all_passed and result
    except Exception as e:
        test_result(
            "GET /matches/pending - Retrieve pending matches",
            False,
            str(e)
        )
        all_passed = False
    
    return all_passed

# ============================================================================
# STEP 7: ERROR CASES & EDGE CASES
# ============================================================================
def test_error_cases():
    print_header("STEP 7: Error Cases & Edge Cases")
    
    token = test_data.get("token")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    all_passed = True
    
    # Test 7.1: Invalid JSON
    print(f"\n{BOLD}Test 7.1: Invalid JSON Payload{RESET}")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data="invalid json {",
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        result = response.status_code in [400, 422]
        test_result(
            "POST /auth/login - Invalid JSON returns 400/422",
            result,
            f"Status: {response.status_code}"
        )
        all_passed = all_passed and result
    except Exception as e:
        test_result(
            "POST /auth/login - Invalid JSON returns 400/422",
            False,
            str(e)
        )
        all_passed = False
    
    # Test 7.2: Non-existent resource
    print(f"\n{BOLD}Test 7.2: Non-existent Resource{RESET}")
    try:
        response = requests.get(
            f"{BASE_URL}/cases/999999999",
            headers=headers,
            timeout=TIMEOUT
        )
        result = response.status_code in [404, 401]
        test_result(
            "GET /cases/{invalid_id} - Returns 404 or 401",
            result,
            f"Status: {response.status_code}"
        )
        all_passed = all_passed and result
    except Exception as e:
        test_result(
            "GET /cases/{invalid_id} - Returns 404 or 401",
            False,
            str(e)
        )
        all_passed = False
    
    # Test 7.3: Missing required fields
    print(f"\n{BOLD}Test 7.3: Missing Required Fields{RESET}")
    try:
        payload = {
            "email": TEST_USER_EMAIL + "2"
            # Missing password
        }
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=payload,
            timeout=TIMEOUT
        )
        result = response.status_code in [400, 422]
        test_result(
            "POST /auth/login - Missing password returns error",
            result,
            f"Status: {response.status_code} (expected 400/422)"
        )
        all_passed = all_passed and result
    except Exception as e:
        test_result(
            "POST /auth/login - Missing password returns error",
            False,
            str(e)
        )
        all_passed = False
    
    # Test 7.4: Duplicate email registration
    print(f"\n{BOLD}Test 7.4: Duplicate Email Registration{RESET}")
    try:
        payload = {
            "first_name": "Duplicate",
            "last_name": "User",
            "email": TEST_USER_EMAIL,  # Same email as earlier
            "password": "Password123"
        }
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json=payload,
            timeout=TIMEOUT
        )
        result = response.status_code in [400, 422, 409]  # Bad Request, Conflict, or Unprocessable
        test_result(
            "POST /auth/register - Duplicate email returns error",
            result,
            f"Status: {response.status_code} (expected 400/422/409)"
        )
        all_passed = all_passed and result
    except Exception as e:
        test_result(
            "POST /auth/register - Duplicate email returns error",
            False,
            str(e)
        )
        all_passed = False
    
    return all_passed

# ============================================================================
# FINAL REPORT
# ============================================================================
def print_final_report():
    print_header("TEST SUMMARY REPORT")
    
    total = len(passed_tests) + len(failed_tests)
    pass_rate = (len(passed_tests) / total * 100) if total > 0 else 0
    
    print(f"{GREEN}{BOLD}Passed:{RESET} {len(passed_tests)}/{total}")
    print(f"{RED}{BOLD}Failed:{RESET} {len(failed_tests)}/{total}")
    print(f"Pass Rate: {pass_rate:.1f}%\n")
    
    if failed_tests:
        print(f"{RED}{BOLD}Failed Tests:{RESET}")
        for test in failed_tests:
            print(f"  • {test}")
    
    if test_data:
        print(f"\n{BOLD}Test Data Summary:{RESET}")
        print(f"  • User Email: {test_data.get('user_email', 'N/A')}")
        print(f"  • Token: {test_data.get('token', 'N/A')[:30]}...")
        if "case_id" in test_data:
            print(f"  • Case ID: {test_data.get('case_id')}")
            print(f"  • Case #: {test_data.get('case_number')}")
    
    print(f"\n{BOLD}Recommendations:{RESET}")
    if len(failed_tests) == 0:
        print(f"  {GREEN}✓ All tests passed! System ready for deployment.{RESET}")
    else:
        print(f"  {YELLOW}Review failed tests and check backend logs.{RESET}")
        print(f"  {YELLOW}Ensure all dependencies are installed.{RESET}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    print(f"\n{BOLD}{BLUE}Missing Person Tracker - QA Test Suite{RESET}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API URL: {BASE_URL}\n")
    
    # Run all tests in sequence
    try:
        # Step 1
        if not test_backend_health():
            print(f"\n{RED}{BOLD}Backend not running. Please start the server.{RESET}")
            print(f"Run: cd backend; python -m uvicorn main:app --reload")
            sys.exit(1)
        
        # Steps 2-7
        test_auth_apis()
        test_protected_apis()
        test_public_apis()
        test_case_filing_flow()
        test_admin_flow()
        test_error_cases()
        
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Tests interrupted by user{RESET}")
    except Exception as e:
        print(f"\n{RED}Unexpected error: {e}{RESET}")
    finally:
        print_final_report()
        print(f"\nEnd Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

if __name__ == "__main__":
    main()
