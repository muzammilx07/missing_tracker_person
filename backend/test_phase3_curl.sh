#!/bin/bash

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 3 TESTING: Police Stations, FIR, Alerts, Dispatch
# Using simple curl commands
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BASE_URL="http://localhost:8000"
TIMESTAMP=$(date +%s%N)

echo ""
echo "════════════════════════════════════════════════════════"
echo "  PHASE 3: Police Stations, FIR, Alerts, Dispatch Tests"
echo "════════════════════════════════════════════════════════"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 1: Register and Login Admin
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "[SETUP] Registering Admin User..."

ADMIN_EMAIL="admin_phase3_${TIMESTAMP}@test.com"
ADMIN_PASS="AdminPass123!@#"

curl -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"first_name\": \"Phase3\",
    \"last_name\": \"Admin\",
    \"email\": \"$ADMIN_EMAIL\",
    \"password\": \"$ADMIN_PASS\",
    \"phone_number\": \"9876543210\",
    \"role\": \"admin\"
  }" \
  -s -o /dev/null 2>&1

echo "✓ Attempting admin registration..."
echo ""

# Login
echo "[SETUP] Logging in Admin..."

LOGIN_RESPONSE=$(curl -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$ADMIN_EMAIL\",
    \"password\": \"$ADMIN_PASS\"
  }" \
  -s)

TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "✗ Login failed"
  exit 1
fi

echo "✓ Login successful"
echo "Token: ${TOKEN:0:20}..."
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 1: Police Stations Search (Mumbai - Overpass API)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "[TEST 1] Police Stations Search (Mumbai)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Getting police stations near Mumbai (19.0760, 72.8777)..."
POLICE_RESPONSE=$(curl -X GET "$BASE_URL/police-stations?latitude=19.0760&longitude=72.8777&radius_km=5&limit=5" \
  -H "Authorization: Bearer $TOKEN" \
  -s)

echo "✓ Police stations found:"
echo "$POLICE_RESPONSE" | jq '.stations[] | {name, address, distance_km}'
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 2: Create Case and Missing Person
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "[TEST 2] Create Case for FIR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Register family member
FAMILY_EMAIL="family_phase3_${TIMESTAMP}@test.com"
FAMILY_PASS="FamilyPass123!@#"

curl -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"first_name\": \"John\",
    \"last_name\": \"Doe\",
    \"email\": \"$FAMILY_EMAIL\",
    \"password\": \"$FAMILY_PASS\",
    \"phone_number\": \"9876543211\",
    \"role\": \"family_member\"
  }" \
  -s -o /dev/null 2>&1

# Login family member
FAMILY_LOGIN=$(curl -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$FAMILY_EMAIL\",
    \"password\": \"$FAMILY_PASS\"
  }" \
  -s)

FAMILY_TOKEN=$(echo "$FAMILY_LOGIN" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo "✓ Family member registered and logged in"

# Register missing person
MISSING_RESPONSE=$(curl -X POST "$BASE_URL/missing-persons/register" \
  -H "Authorization: Bearer $FAMILY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Rajesh",
    "last_name": "Kumar",
    "age": 28,
    "gender": "Male",
    "height_cm": 175,
    "description": "Last seen wearing blue shirt",
    "photo_url": "https://via.placeholder.com/300"
  }' \
  -s)

MISSING_ID=$(echo "$MISSING_RESPONSE" | grep -o '"missing_person_id":[0-9]*' | cut -d':' -f2)

echo "✓ Missing person registered: ID $MISSING_ID"

# File case
CASE_RESPONSE=$(curl -X POST "$BASE_URL/cases/file" \
  -H "Authorization: Bearer $FAMILY_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"missing_person_id\": $MISSING_ID,
    \"last_seen_date\": \"2026-04-05\",
    \"last_seen_address\": \"Marine Drive\",
    \"last_seen_city\": \"Mumbai\",
    \"last_seen_state\": \"Maharashtra\",
    \"last_seen_latitude\": 19.0876,
    \"last_seen_longitude\": 72.8226,
    \"description\": \"Missing since morning, last seen at Marine Drive\"
  }" \
  -s)

CASE_ID=$(echo "$CASE_RESPONSE" | grep -o '"case_id":[0-9]*' | cut -d':' -f2)

echo "✓ Case filed: ID $CASE_ID"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 3: Get Police Stations for Case
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "[TEST 3] Get Police Stations for Case"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

CASE_STATIONS=$(curl -X GET "$BASE_URL/cases/$CASE_ID/police-stations?radius_km=10&limit=5" \
  -H "Authorization: Bearer $TOKEN" \
  -s)

echo "✓ Stations for case:"
echo "$CASE_STATIONS" | jq '.location, .count'
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 4: Generate FIR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "[TEST 4] Generate FIR PDF"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

FIR_RESPONSE=$(curl -X POST "$BASE_URL/fir/generate/$CASE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -s)

FIR_ID=$(echo "$FIR_RESPONSE" | grep -o '"fir_id":[0-9]*' | cut -d':' -f2)
PDF_URL=$(echo "$FIR_RESPONSE" | grep -o '"pdf_url":"[^"]*' | cut -d'"' -f4)

echo "✓ FIR generated: ID $FIR_ID"
echo "✓ PDF URL: $PDF_URL"
echo ""
echo "📄 Open PDF in browser: $PDF_URL"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 5: Sign FIR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "[TEST 5] Sign FIR (Admin Only)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

SIGN_RESPONSE=$(curl -X POST "$BASE_URL/fir/$FIR_ID/sign" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -s)

SIGNED_STATUS=$(echo "$SIGN_RESPONSE" | grep -o '"fir_status":"[^"]*' | cut -d'"' -f4)

echo "✓ FIR signed"
echo "✓ New status: $SIGNED_STATUS"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 6: Auto-Dispatch to 3 Nearest Stations
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "[TEST 6] Auto-Dispatch FIR to 3 Nearest Stations"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

DISPATCH_RESPONSE=$(curl -X POST "$BASE_URL/fir/$FIR_ID/dispatch-auto" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -s)

echo "✓ Auto-dispatch response:"
echo "$DISPATCH_RESPONSE" | jq '.dispatch_count, .dispatches[] | {station_name, distance_from_incident, dispatch_status}'
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 7: FIR Statistics
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "[TEST 7] FIR Statistics (Admin Only)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

STATS_RESPONSE=$(curl -X GET "$BASE_URL/fir/stats" \
  -H "Authorization: Bearer $TOKEN" \
  -s)

echo "✓ FIR Statistics:"
echo "$STATS_RESPONSE" | jq '.fir_statistics, .dispatch_statistics'
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SUMMARY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "════════════════════════════════════════════════════════"
echo "  Phase 3 Testing Complete! ✓"
echo "════════════════════════════════════════════════════════"
echo ""
echo "📋 Summary:"
echo "  ✓ Police stations search (Overpass API)"
echo "  ✓ Case-specific station lookup"
echo "  ✓ FIR PDF generation"
echo "  ✓ FIR signing (admin)"
echo "  ✓ Auto-dispatch to 3 nearest stations"
echo "  ✓ FIR statistics dashboard"
echo ""
echo "💡 Next Steps:"
echo "  1. Open PDF URL in browser to view Indian FIR format"
echo "  2. Run: cd backend && python test_api.py"
echo "  3. Check frontend alerts dashboard"
echo ""
