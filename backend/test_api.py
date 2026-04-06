"""
Comprehensive Test Cases for Missing Person Tracker API
Tests all endpoints systematically with various scenarios
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
admin_token = None
user_token = None
user2_token = None
admin_user_id = None
regular_user_id = None
case_id = None
sighting_id = None
match_id = None


def print_test(test_name: str, result: bool, details: str = ""):
    """Helper to print test results"""
    status = "[PASS]" if result else "[FAIL]"
    print(f"{status} | {test_name}")
    if details:
        print(f"      └─ {details}")


def print_section(title: str):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HEALTH & ROOT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_health():
    """Test health check endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    result = response.status_code == 200 and response.json()["status"] == "ok"
    print_test("Health Check", result, f"Status: {response.status_code}")
    return result


def test_root():
    """Test root endpoint"""
    response = requests.get(f"{BASE_URL}/")
    result = response.status_code == 200 and "version" in response.json()
    print_test("Root Endpoint", result, f"Status: {response.status_code}")
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUTH ROUTES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_auth_register():
    """Test user registration"""
    global user_token, regular_user_id
    
    import random
    email = f"testuser{random.randint(10000,99999)}@example.com"
    payload = {
        "name": "Test User",
        "email": email,
        "password": "TestPass@123",
        "phone": "1234567890"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    result = response.status_code == 200
    if result:
        data = response.json()
        user_token = data.get("token")
        regular_user_id = data.get("id")
    else:
        print(f"      └─ DEBUG: Response: {response.text[:200]}")
    print_test("Register User", result, f"Status: {response.status_code}, Token: {'✓' if user_token else '✗'}")
    return result


def test_auth_register_duplicate():
    """Test duplicate email registration fails"""
    payload = {
        "name": "Another User",
        "email": "testuser@example.com",  # Same as above
        "password": "AnotherPass@123"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    result = response.status_code == 400
    print_test("Duplicate Email Rejection", result, f"Status: {response.status_code}")
    return result


def test_auth_login():
    """Test user login"""
    global admin_token, admin_user_id
    
    payload = {
        "email": "admin@example.com",
        "password": "Admin@1234"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=payload)
    result = response.status_code == 200
    if result:
        data = response.json()
        admin_token = data.get("token")
        admin_user_id = data.get("id")
    print_test("Admin Login", result, f"Status: {response.status_code}, Token: {'✓' if admin_token else '✗'}")
    return result


def test_auth_login_invalid():
    """Test invalid credentials"""
    payload = {
        "email": "admin@example.com",
        "password": "wrongpassword"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=payload)
    result = response.status_code == 401
    print_test("Invalid Credentials", result, f"Status: {response.status_code}")
    return result


def test_auth_me():
    """Test getting current user info"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    result = response.status_code == 200 and response.json()["email"] == "admin@example.com"
    print_test("Get Current User", result, f"Status: {response.status_code}")
    return result


def test_auth_me_unauthorized():
    """Test unauthorized access"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    result = response.status_code == 401
    print_test("Unauthorized Access", result, f"Status: {response.status_code}")
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CASES ROUTES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_create_case():
    """Test creating a missing person case"""
    global case_id
    
    if not user_token:
        print_test("Create Case", False, "Skipped: user_token not available")
        return False
    
    # Create a simple test image
    image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    
    files = {'photo': ('test.png', image_data, 'image/png')}
    data = {
        'full_name': 'John Doe',
        'age': 25,
        'gender': 'Male',
        'last_seen_date': '2026-04-05',
        'last_seen_city': 'Mumbai',
        'last_seen_state': 'Maharashtra',
        'last_seen_address': 'CST Station',
        'description': 'Wearing blue shirt',
        'police_dispatch_mode': 'manual'
    }
    
    headers = {"Authorization": f"Bearer {user_token}"}
    response = requests.post(f"{BASE_URL}/cases", files=files, data=data, headers=headers)
    result = response.status_code == 200
    if result:
        case_id = response.json().get("case_id")
    else:
        print(f"      └─ DEBUG: Response: {response.text[:200]}")
    print_test("Create Case", result, f"Status: {response.status_code}, Case ID: {case_id}")
    return result


def test_list_cases():
    """Test listing cases"""
    if not user_token:
        print_test("List Cases", False, "Skipped: user_token not available")
        return False
    headers = {"Authorization": f"Bearer {user_token}"}
    response = requests.get(f"{BASE_URL}/cases", headers=headers)
    result = response.status_code == 200 and "cases" in response.json()
    print_test("List Cases", result, f"Status: {response.status_code}, Cases: {len(response.json().get('cases', []))}")
    return result


def test_get_case():
    """Test getting single case details"""
    if not case_id:
        print_test("Get Case Details", False, "Skipped: case_id not available")
        return False
    headers = {"Authorization": f"Bearer {user_token}"}
    response = requests.get(f"{BASE_URL}/cases/{case_id}", headers=headers)
    result = response.status_code == 200 and response.json()["id"] == case_id
    print_test("Get Case Details", result, f"Status: {response.status_code}")
    return result


def test_update_case_status():
    """Test updating case status (admin only)"""
    if not case_id:
        print_test("Update Case Status", False, "Skipped: case_id not available")
        return False
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {"status": "under_investigation"}
    response = requests.patch(f"{BASE_URL}/cases/{case_id}/status", json=payload, headers=headers)
    result = response.status_code == 200
    print_test("Update Case Status", result, f"Status: {response.status_code}")
    return result


def test_update_dispatch_mode():
    """Test updating police dispatch mode"""
    if not case_id:
        print_test("Update Dispatch Mode", False, "Skipped: case_id not available")
        return False
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {"mode": "auto"}
    response = requests.patch(f"{BASE_URL}/cases/{case_id}/dispatch-mode", json=payload, headers=headers)
    result = response.status_code == 200
    print_test("Update Dispatch Mode", result, f"Status: {response.status_code}")
    return result


def test_add_family_member():
    """Test adding family member to case"""
    if not case_id or not user_token:
        print_test("Add Family Member", False, "Skipped: case_id or user_token not available")
        return False
    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {"email": "testuser@example.com"}  # The registered user
    response = requests.post(f"{BASE_URL}/cases/{case_id}/family", json=payload, headers=headers)
    result = response.status_code == 200
    print_test("Add Family Member", result, f"Status: {response.status_code}")
    return result


def test_case_realtime():
    """Test getting realtime case updates"""
    if not case_id:
        print_test("Get Case Realtime", False, "Skipped: case_id not available")
        return False
    headers = {"Authorization": f"Bearer {user_token}"}
    response = requests.get(f"{BASE_URL}/cases/{case_id}/realtime", headers=headers)
    result = response.status_code == 200 and "timeline" in response.json()
    try:
        events = len(response.json().get('timeline', []))
    except:
        events = 0
    print_test("Get Case Realtime", result, f"Status: {response.status_code}, Timeline Events: {events}")
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIGHTINGS ROUTES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_create_sighting():
    """Test reporting a sighting (public endpoint)"""
    global sighting_id
    
    image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    
    files = {'photo': ('sighting.png', image_data, 'image/png')}
    data = {
        'sighting_lat': 19.0760,
        'sighting_lng': 72.8777,
        'reporter_name': 'Witness Name',
        'reporter_phone': '9876543210'
    }
    
    response = requests.post(f"{BASE_URL}/sightings", files=files, data=data)
    result = response.status_code == 200
    if result:
        sighting_id = response.json().get("sighting_id")
    else:
        print(f"      └─ DEBUG: Status {response.status_code}, Response: {response.text[:300]}")
    print_test("Create Sighting (Public)", result, f"Status: {response.status_code}, Sighting ID: {sighting_id}")
    return result


def test_list_sightings():
    """Test listing sightings (admin only)"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BASE_URL}/sightings", headers=headers)
    result = response.status_code == 200
    try:
        count = len(response.json().get('sightings', []))
    except:
        print(f"      └─ DEBUG: Response status {response.status_code}, body: {response.text[:300]}")
        count = 0
    print_test("List Sightings", result, f"Status: {response.status_code}, Count: {count}")
    return result


def test_get_sighting():
    """Test getting sighting details"""
    if not sighting_id:
        print_test("Get Sighting Details", False, "Skipped: sighting_id not available")
        return False
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BASE_URL}/sightings/{sighting_id}", headers=headers)
    result = response.status_code == 200
    print_test("Get Sighting Details", result, f"Status: {response.status_code}")
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MATCHES ROUTES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_list_matches():
    """Test listing matches"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BASE_URL}/matches", headers=headers)
    result = response.status_code == 200
    print_test("List Matches", result, f"Status: {response.status_code}, Matches: {len(response.json().get('matches', []))}")
    return result


def test_pending_count():
    """Test getting pending match count"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BASE_URL}/matches/pending-count", headers=headers)
    result = response.status_code == 200
    if not result:
        print(f"      └─ DEBUG: Status {response.status_code}, Response: {response.text[:300]}")
    print_test("Pending Match Count", result, f"Status: {response.status_code}")
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VOLUNTEERS ROUTES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_apply_volunteer():
    """Test volunteer application"""
    if not user_token:
        print_test("Apply as Volunteer", False, "Skipped: user_token not available")
        return False
    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {
        "coverage_type": "city",
        "coverage_city": "Mumbai",
        "bio": "Enthusiastic volunteer"
    }
    response = requests.post(f"{BASE_URL}/volunteers/apply", json=payload, headers=headers)
    result = response.status_code == 200
    print_test("Apply as Volunteer", result, f"Status: {response.status_code}")
    return result


def test_list_volunteers():
    """Test listing volunteers (admin)"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BASE_URL}/volunteers", headers=headers)
    result = response.status_code == 200
    try:
        count = len(response.json().get('volunteers', []))
    except:
        count = 0
    print_test("List Volunteers", result, f"Status: {response.status_code}, Volunteers: {count}")
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ADMIN ROUTES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_admin_stats():
    """Test admin dashboard stats"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BASE_URL}/admin/stats", headers=headers)
    result = response.status_code == 200 and "cases" in response.json()
    print_test("Admin Stats", result, f"Status: {response.status_code}")
    return result


def test_admin_test():
    """Test admin-only endpoint"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BASE_URL}/admin/test", headers=headers)
    result = response.status_code == 200
    print_test("Admin Test Route", result, f"Status: {response.status_code}")
    return result


def test_notifications():
    """Test getting notifications"""
    headers = {"Authorization": f"Bearer {user_token}"}
    response = requests.get(f"{BASE_URL}/notifications", headers=headers)
    result = response.status_code == 200
    print_test("Get Notifications", result, f"Status: {response.status_code}")
    return result


def test_notifications_count():
    """Test getting notification count"""
    headers = {"Authorization": f"Bearer {user_token}"}
    response = requests.get(f"{BASE_URL}/notifications/count", headers=headers)
    result = response.status_code == 200
    print_test("Notification Count", result, f"Status: {response.status_code}")
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN TEST RUNNER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_all_tests():
    """Run all test cases"""
    
    print("\n" + "="*60)
    print("  MISSING PERSON TRACKER API - COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    tests = []
    
    # Health & Root
    print_section("Health & Root Endpoints")
    tests.append(("Health Check", test_health()))
    tests.append(("Root Endpoint", test_root()))
    
    # Auth
    print_section("Authentication Routes")
    tests.append(("Register User", test_auth_register()))
    tests.append(("Duplicate Email", test_auth_register_duplicate()))
    tests.append(("Login", test_auth_login()))
    tests.append(("Invalid Credentials", test_auth_login_invalid()))
    tests.append(("Get Current User", test_auth_me()))
    tests.append(("Unauthorized Access", test_auth_me_unauthorized()))
    
    # Cases
    print_section("Cases Routes")
    tests.append(("Create Case", test_create_case()))
    tests.append(("List Cases", test_list_cases()))
    tests.append(("Get Case", test_get_case()))
    tests.append(("Update Case Status", test_update_case_status()))
    tests.append(("Update Dispatch Mode", test_update_dispatch_mode()))
    tests.append(("Add Family Member", test_add_family_member()))
    tests.append(("Case Realtime", test_case_realtime()))
    
    # Sightings
    print_section("Sightings Routes")
    tests.append(("Create Sighting", test_create_sighting()))
    tests.append(("List Sightings", test_list_sightings()))
    tests.append(("Get Sighting", test_get_sighting()))
    
    # Matches
    print_section("Matches Routes")
    tests.append(("List Matches", test_list_matches()))
    tests.append(("Pending Count", test_pending_count()))
    
    # Volunteers
    print_section("Volunteers Routes")
    tests.append(("Apply Volunteer", test_apply_volunteer()))
    tests.append(("List Volunteers", test_list_volunteers()))
    
    # Admin
    print_section("Admin Routes")
    tests.append(("Admin Stats", test_admin_stats()))
    tests.append(("Admin Test", test_admin_test()))
    tests.append(("Notifications", test_notifications()))
    tests.append(("Notification Count", test_notifications_count()))
    
    # Summary
    print_section("Test Summary")
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    print(f"[PASS] Passed: {passed}/{total}")
    print(f"[FAIL] Failed: {total - passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n*** ALL TESTS PASSED! ***")
    else:
        print(f"\n*** WARNING: {total - passed} test(s) failed ***")


if __name__ == "__main__":
    run_all_tests()
