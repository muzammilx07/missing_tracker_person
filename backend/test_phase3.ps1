# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 3 TESTING: Police Stations, FIR, Alerts, Dispatch  
# Simple curl-based testing
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

$BASE_URL = "http://localhost:8000"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$testFile = "test_$timestamp.ps1"

Write-Host "`n" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  PHASE 3: Police Stations, FIR, Alerts, Dispatch Tests" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "`n"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Helper Functions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Url,
        [string]$Token,
        [string]$Body = $null,
        [int]$ExpectedStatus = 200
    )
    
    Write-Host "▶ $Name" -ForegroundColor Yellow
    Write-Host "  $Method $Url" -ForegroundColor DarkGray
    
    try {
        $headers = @{
            "Authorization" = "Bearer $Token"
            "Content-Type" = "application/json"
        }
        
        $params = @{
            Uri = $Url
            Method = $Method
            Headers = $headers
            UseBasicParsing = $true
        }
        
        if ($Body) {
            $params["Body"] = $Body
        }
        
        $response = Invoke-WebRequest @params
        
        Write-Host "  ✓ Status: $($response.StatusCode)" -ForegroundColor Green
        
        if ($response.Content) {
            $jsonResponse = $response.Content | ConvertFrom-Json
            return $jsonResponse
        }
        return $response
    }
    catch {
        if ($_.Exception.Response) {
            $statusCode = $_.Exception.Response.StatusCode.Value__
            Write-Host "  ✗ Error: $statusCode - $($_.Exception.Message)" -ForegroundColor Red
            if ($_.Exception.Response.Content) {
                $errorContent = $_.Exception.Response.Content | ConvertFrom-Json
                Write-Host "  Details: $($errorContent.detail)" -ForegroundColor Red
            }
        }
        else {
            Write-Host "  ✗ Error: $($_.Exception.Message)" -ForegroundColor Red
        }
        return $null
    }
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SETUP: Register/Login Admin User
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "`n[SETUP] Creating Admin User..." -ForegroundColor Magenta
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta

$adminEmail = "admin_phase3_$timestamp@test.com"
$adminPassword = "AdminPass123!@#"

# Register admin
$registerBody = @{
    first_name = "Phase3"
    last_name = "Admin"
    email = $adminEmail
    password = $adminPassword
    phone_number = "9876543210"
    role = "admin"
} | ConvertTo-Json

$registerUrl = "$BASE_URL/auth/register"
Write-Host "▶ Register Admin" -ForegroundColor Yellow
Write-Host "  POST $registerUrl" -ForegroundColor DarkGray

try {
    $registerResponse = Invoke-WebRequest -Uri $registerUrl -Method POST -Body $registerBody -Headers @{"Content-Type" = "application/json"} -UseBasicParsing
    Write-Host "  ✓ Status: $($registerResponse.StatusCode)" -ForegroundColor Green
}
catch {
    Write-Host "  ℹ Admin may already exist, logging in..." -ForegroundColor Cyan
}

# Login
$loginBody = @{
    email = $adminEmail
    password = $adminPassword
} | ConvertTo-Json

$loginUrl = "$BASE_URL/auth/login"
$loginResponse = Test-Endpoint -Name "Login Admin" -Method "POST" -Url $loginUrl -Token "" -Body $loginBody

if ($null -eq $loginResponse) {
    Write-Host "`n✗ Login failed. Exiting." -ForegroundColor Red
    exit 1
}

$TOKEN = $loginResponse.access_token
Write-Host "  Token: $($TOKEN.Substring(0, 20))..." -ForegroundColor Cyan

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 1: Police Stations Search (Overpass API)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "`n[TEST 1] Police Stations Search (Mumbai)" -ForegroundColor Magenta
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta

$policeStationsUrl = '$BASE_URL/police-stations?latitude=19.0760&longitude=72.8777&radius_km=5&limit=5' -replace '\$BASE_URL', $BASE_URL
$policeStations = Test-Endpoint -Name "Get Police Stations (Mumbai)" -Method "GET" -Url $policeStationsUrl -Token $TOKEN

if ($policeStations) {
    Write-Host "  Found $($policeStations.count) stations" -ForegroundColor Cyan
    if ($policeStations.stations.Count -gt 0) {
        Write-Host "`n  Stations:" -ForegroundColor Cyan
        $policeStations.stations | ForEach-Object {
            Write-Host "    • $($_.name) - $($_.address)" -ForegroundColor DarkCyan
            Write-Host "      OSM: $($_.osm_url)" -ForegroundColor DarkGray
        }
    }
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 2: Create Case for FIR Testing
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "`n[TEST 2] Create Case for FIR" -ForegroundColor Magenta
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta

# Register family member (case reporter)
$familyEmail = "family_phase3_$timestamp@test.com"
$familyPassword = "FamilyPass123!@#"

$familyRegisterBody = @{
    first_name = "John"
    last_name = "Doe"
    email = $familyEmail
    password = $familyPassword
    phone_number = "9876543211"
    role = "family_member"
} | ConvertTo-Json

$registerUrl = "$BASE_URL/auth/register"
try {
    Invoke-WebRequest -Uri $registerUrl -Method POST -Body $familyRegisterBody -Headers @{"Content-Type" = "application/json"} -UseBasicParsing | Out-Null
}
catch {
    Write-Host "  ℹ Family member may already exist" -ForegroundColor Cyan
}

# Login as family member
$familyLoginBody = @{
    email = $familyEmail
    password = $familyPassword
} | ConvertTo-Json

$familyLoginResponse = Test-Endpoint -Name "Login Family Member" -Method "POST" -Url $loginUrl -Token "" -Body $familyLoginBody
$FAMILY_TOKEN = $familyLoginResponse.access_token
Write-Host "  Family Token: $($FAMILY_TOKEN.Substring(0, 20))..." -ForegroundColor Cyan

# Register missing person
$caseBody = @{
    first_name = "Rajesh"
    last_name = "Kumar"
    age = 28
    gender = "Male"
    height_cm = 175
    description = "Last seen wearing blue shirt"
    photo_url = "https://via.placeholder.com/300"
} | ConvertTo-Json

$missingPersonUrl = "$BASE_URL/missing-persons/register"
$missingPerson = Test-Endpoint -Name "Register Missing Person" -Method "POST" -Url $missingPersonUrl -Token $FAMILY_TOKEN -Body $caseBody

if ($null -eq $missingPerson) {
    Write-Host "`n✗ Failed to create missing person. Exiting." -ForegroundColor Red
    exit 1
}

$missingPersonId = $missingPerson.missing_person_id
Write-Host "  Missing Person ID: $missingPersonId" -ForegroundColor Cyan

# File case
$fileBody = @{
    missing_person_id = $missingPersonId
    last_seen_date = "2026-04-05"
    last_seen_address = "Marine Drive"
    last_seen_city = "Mumbai"
    last_seen_state = "Maharashtra"
    last_seen_latitude = 19.0876
    last_seen_longitude = 72.8226
    description = "Missing since morning, last seen at Marine Drive. Unknown persons spotted nearby."
} | ConvertTo-Json

$fileCaseUrl = "$BASE_URL/cases/file"
$case = Test-Endpoint -Name "File Case" -Method "POST" -Url $fileCaseUrl -Token $FAMILY_TOKEN -Body $fileBody

if ($null -eq $case) {
    Write-Host "`n✗ Failed to file case. Exiting." -ForegroundColor Red
    exit 1
}

$CASE_ID = $case.case_id
Write-Host "  Case ID: $CASE_ID" -ForegroundColor Cyan

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 3: Get Police Stations for Case
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "`n[TEST 3] Get Police Stations for Specific Case" -ForegroundColor Magenta
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta

$caseStationsUrl = "$BASE_URL/cases/$CASE_ID/police-stations?radius_km=10&limit=5"
$caseStations = Test-Endpoint -Name "Get Stations for Case" -Method "GET" -Url $caseStationsUrl -Token $TOKEN

if ($caseStations) {
    Write-Host "  Case Location: $($caseStations.location.city), $($caseStations.location.state)" -ForegroundColor Cyan
    Write-Host "  Found $($caseStations.count) nearby stations" -ForegroundColor Cyan
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 4: Generate FIR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "`n[TEST 4] Generate FIR PDF" -ForegroundColor Magenta
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta

$generateFirUrl = "$BASE_URL/fir/generate/$CASE_ID"
$fir = Test-Endpoint -Name "Generate FIR" -Method "POST" -Url $generateFirUrl -Token $TOKEN

if ($fir) {
    $FIR_ID = $fir.fir_id
    Write-Host "  FIR ID: $FIR_ID" -ForegroundColor Cyan
    Write-Host "  Status: $($fir.fir_status)" -ForegroundColor Cyan
    Write-Host "  PDF URL: $($fir.pdf_url)" -ForegroundColor Green
    Write-Host "`n  📄 Open PDF in browser: $($fir.pdf_url)" -ForegroundColor Green
}
else {
    Write-Host "`n✗ FIR generation failed." -ForegroundColor Red
    exit 1
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 5: Get FIR Details
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "`n[TEST 5] Get FIR Details" -ForegroundColor Magenta
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta

$firDetailsUrl = "$BASE_URL/fir/$FIR_ID"
$firDetails = Test-Endpoint -Name "Get FIR Details" -Method "GET" -Url $firDetailsUrl -Token $TOKEN

if ($firDetails) {
    Write-Host "  FIR Status: $($firDetails.fir_status)" -ForegroundColor Cyan
    Write-Host "  Signed By: $($firDetails.signed_by)" -ForegroundColor Cyan
    Write-Host "  Dispatches: $($firDetails.dispatch_count)" -ForegroundColor Cyan
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 6: Sign FIR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "`n[TEST 6] Sign FIR (Admin Only)" -ForegroundColor Magenta
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta

$signFirUrl = "$BASE_URL/fir/$FIR_ID/sign"
$signedFir = Test-Endpoint -Name "Sign FIR" -Method "POST" -Url $signFirUrl -Token $TOKEN

if ($signedFir) {
    Write-Host "  New Status: $($signedFir.fir_status)" -ForegroundColor Green
    Write-Host "  Signed By: $($signedFir.signed_by)" -ForegroundColor Green
    Write-Host "  Signed At: $($signedFir.signed_at)" -ForegroundColor Green
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 7: Auto-Dispatch FIR to Nearest Stations
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "`n[TEST 7] Auto-Dispatch FIR to 3 Nearest Stations" -ForegroundColor Magenta
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta

$dispatchAutoUrl = "$BASE_URL/fir/$FIR_ID/dispatch-auto"
$dispatch = Test-Endpoint -Name "Auto-Dispatch FIR" -Method "POST" -Url $dispatchAutoUrl -Token $TOKEN

if ($dispatch) {
    Write-Host "  Dispatched to $($dispatch.dispatch_count) stations" -ForegroundColor Green
    Write-Host "`n  Dispatch Details:" -ForegroundColor Cyan
    $dispatch.dispatches | ForEach-Object {
        Write-Host "    • $($_.station_name)" -ForegroundColor DarkCyan
        Write-Host "      Address: $($_.station_address)" -ForegroundColor DarkGray
        Write-Host "      Distance: $($_.distance_from_incident)" -ForegroundColor DarkGray
        Write-Host "      Status: $($_.dispatch_status)" -ForegroundColor Cyan
    }
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 8: Manual Dispatch Test
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "`n[TEST 8] Manual Dispatch to Specific Station" -ForegroundColor Magenta
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta

# Get first station from police stations search
if ($policeStations -and $policeStations.stations.Count -gt 0) {
    $station = $policeStations.stations[0]
    
    $manualDispatchUrl = "$BASE_URL/fir/$FIR_ID/dispatch"
    $manualDispatchUrl = $manualDispatchUrl + "?station_name=$([Uri]::EscapeDataString($station.name))"
    $manualDispatchUrl = $manualDispatchUrl + "&" + "station_latitude=$($station.lat)"
    $manualDispatchUrl = $manualDispatchUrl + "&" + "station_longitude=$($station.lng)"
    $manualDispatchUrl = $manualDispatchUrl + "&" + "station_address=$([Uri]::EscapeDataString($station.address))"
    
    $manualDispatch = Test-Endpoint -Name "Manual Dispatch" -Method "POST" -Url $manualDispatchUrl -Token $TOKEN
    
    if ($manualDispatch) {
        Write-Host "  Dispatch ID: $($manualDispatch.dispatch_id)" -ForegroundColor Green
        Write-Host "  Station: $($manualDispatch.station_name)" -ForegroundColor Cyan
        Write-Host "  Status: $($manualDispatch.dispatch_status)" -ForegroundColor Green
    }
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 9: FIR Statistics
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "`n[TEST 9] FIR Statistics (Admin Only)" -ForegroundColor Magenta
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta

$statsUrl = "$BASE_URL/fir/stats"
$stats = Test-Endpoint -Name "Get FIR Statistics" -Method "GET" -Url $statsUrl -Token $TOKEN

if ($stats) {
    Write-Host "`n  FIR Statistics:" -ForegroundColor Cyan
    Write-Host "    Total FIRs: $($stats.fir_statistics.total_firs)" -ForegroundColor DarkCyan
    Write-Host "    Draft: $($stats.fir_statistics.draft)" -ForegroundColor DarkCyan
    Write-Host "    Signed: $($stats.fir_statistics.signed)" -ForegroundColor DarkCyan
    Write-Host "`n  Dispatch Statistics:" -ForegroundColor Cyan
    Write-Host "    Total Dispatches: $($stats.dispatch_statistics.total_dispatches)" -ForegroundColor DarkCyan
    Write-Host "    Dispatched: $($stats.dispatch_statistics.dispatched)" -ForegroundColor DarkCyan
    Write-Host "    Received: $($stats.dispatch_statistics.received)" -ForegroundColor DarkCyan
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SUMMARY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "`n" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Phase 3 Testing Complete! ✓" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan

Write-Host "`n📋 Summary:" -ForegroundColor Yellow
Write-Host "  ✓ Police stations search (Overpass API)" -ForegroundColor Green
Write-Host "  ✓ Case-specific station lookup" -ForegroundColor Green
Write-Host "  ✓ FIR PDF generation" -ForegroundColor Green
Write-Host "  ✓ FIR signing (admin)" -ForegroundColor Green
Write-Host "  ✓ Auto-dispatch to 3 nearest stations" -ForegroundColor Green
Write-Host "  ✓ Manual station dispatch" -ForegroundColor Green
Write-Host "  ✓ FIR statistics dashboard" -ForegroundColor Green

Write-Host "`n🔗 Important URLs:" -ForegroundColor Yellow
Write-Host "  FIR PDF: $($fir.pdf_url)" -ForegroundColor Cyan
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Cyan

Write-Host "`n💡 Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Open PDF URL in browser to view Indian FIR format" -ForegroundColor DarkYellow
Write-Host "  2. Check alerts by visiting frontend alert dashboard" -ForegroundColor DarkYellow
Write-Host "  3. Run test_api.py to verify all endpoints work" -ForegroundColor DarkYellow

Write-Host "`n"
