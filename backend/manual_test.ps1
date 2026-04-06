# Manual Testing Script - Missing Person Tracker API
# Tests core workflows with proper PowerShell commands

Write-Host "`n===============================================" -ForegroundColor Cyan
Write-Host "  MANUAL API TESTING - MISSING PERSON TRACKER" -ForegroundColor Cyan
Write-Host "===============================================`n" -ForegroundColor Cyan

$BASE_URL = "http://localhost:8000"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. CREATE TEST IMAGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "[1/7] Creating test image..." -ForegroundColor Yellow

$imagePath = "$PSScriptRoot\test_person.png"

# Create a simple 1x1 PNG in PowerShell
$pngBytes = [byte[]]@(
    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
    0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
    0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
    0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41,
    0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
    0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,
    0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,
    0x42, 0x60, 0x82
)

[System.IO.File]::WriteAllBytes($imagePath, $pngBytes)
Write-Host "[OK] Test image created at: $imagePath`n" -ForegroundColor Green

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. GET ADMIN TOKEN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "[2/7] Getting admin token..." -ForegroundColor Yellow

try {
    $adminBody = @{
        email = "admin@example.com"
        password = "Admin@1234"
    } | ConvertTo-Json

    $adminResp = Invoke-WebRequest -Uri "$BASE_URL/auth/login" `
        -Method POST `
        -Headers @{"Content-Type"="application/json"} `
        -Body $adminBody -UseBasicParsing -ErrorAction Stop

    $adminData = $adminResp.Content | ConvertFrom-Json
    $ADMIN_TOKEN = $adminData.token
    Write-Host "[OK] Admin token acquired`n" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to get admin token: $_`n" -ForegroundColor Red
    exit 1
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. REGISTER TEST USER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "[3/7] Registering test user (Priya Sharma)..." -ForegroundColor Yellow

try {
    # Generate unique email to avoid conflicts from previous runs
    $timestamp = Get-Date -Format "yyyyMMddHHmmss"
    $uniqueEmail = "priya.test+$timestamp@test.com"
    
    $registerBody = @{
        name = "Priya Sharma"
        email = $uniqueEmail
        password = "Test@1234"
        phone = "9876543210"
    } | ConvertTo-Json

    $userResp = Invoke-WebRequest -Uri "$BASE_URL/auth/register" `
        -Method POST `
        -Headers @{"Content-Type"="application/json"} `
        -Body $registerBody -UseBasicParsing -ErrorAction Stop

    $userData = $userResp.Content | ConvertFrom-Json
    $USER_TOKEN = $userData.token
    $USER_ID = $userData.id

    Write-Host "[OK] User registered:" -ForegroundColor Green
    Write-Host "     Email: $uniqueEmail"
    Write-Host "     User ID: $USER_ID`n"
} catch {
    Write-Host "[ERROR] Failed to register user: $_`n" -ForegroundColor Red
    exit 1
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. FILE A CASE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "[4/7] Filing missing person case (Rahul Verma)..." -ForegroundColor Yellow

try {
    $form = @{
        full_name = "Rahul Verma"
        age = "28"
        gender = "Male"
        last_seen_date = "2026-04-05"
        last_seen_city = "Mumbai"
        last_seen_state = "Maharashtra"
        last_seen_address = "Marine Drive"
        description = "Wearing red shirt"
        police_dispatch_mode = "manual"
        photo = Get-Item -Path $imagePath
    }

    $caseResp = Invoke-WebRequest -Uri "$BASE_URL/cases" `
        -Method POST `
        -Headers @{"Authorization"="Bearer $USER_TOKEN"} `
        -Form $form -UseBasicParsing -ErrorAction Stop

    $caseData = $caseResp.Content | ConvertFrom-Json
    $CASE_ID = $caseData.case_id

    Write-Host "[OK] Case filed:" -ForegroundColor Green
    Write-Host "     Case ID: $CASE_ID"
    Write-Host "     Missing Person: Rahul Verma`n"
} catch {
    Write-Host "[ERROR] Failed to file case: $_`n" -ForegroundColor Red
    exit 1
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. SUBMIT PUBLIC SIGHTING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "[5/7] Submitting public sighting (same photo)..." -ForegroundColor Yellow

try {
    $sightingForm = @{
        sighting_lat = "19.0760"
        sighting_lng = "72.8777"
        reporter_name = "Witness"
        reporter_phone = "9988776655"
        photo = Get-Item -Path $imagePath
    }

    $sightingResp = Invoke-WebRequest -Uri "$BASE_URL/sightings" `
        -Method POST `
        -Form $sightingForm -UseBasicParsing -ErrorAction Stop

    $sightingData = $sightingResp.Content | ConvertFrom-Json
    $SIGHTING_ID = $sightingData.sighting_id
    $MATCHES_FOUND = $sightingData.matches_found

    Write-Host "[OK] Sighting reported:" -ForegroundColor Green
    Write-Host "     Sighting ID: $SIGHTING_ID"
    Write-Host "     Location: Mumbai (19.0760, 72.8777)"
    Write-Host "     Matches Found: $MATCHES_FOUND`n"

    if ($MATCHES_FOUND -gt 0) {
        Write-Host "     >>> MATCH DETECTED! <<<" -ForegroundColor Cyan
    }
} catch {
    Write-Host "[ERROR] Failed to submit sighting: $_`n" -ForegroundColor Red
    exit 1
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. ADMIN CHECKS MATCHES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "[6/7] Admin checking matches..." -ForegroundColor Yellow

try {
    $matchesResp = Invoke-WebRequest -Uri "$BASE_URL/matches" `
        -Method GET `
        -Headers @{"Authorization"="Bearer $ADMIN_TOKEN"} -UseBasicParsing -ErrorAction Stop

    $matchesData = $matchesResp.Content | ConvertFrom-Json
    $TOTAL_MATCHES = $matchesData.total

    Write-Host "[OK] Matches retrieved:" -ForegroundColor Green
    Write-Host "     Total Matches: $TOTAL_MATCHES`n"

    if ($matchesData.matches.Count -gt 0) {
        foreach ($match in $matchesData.matches) {
            Write-Host "     Match #$($match.id):" -ForegroundColor Cyan
            Write-Host "       - Case: $($match.case_id)"
            Write-Host "       - Confidence: $($match.confidence) ($($match.label))"
            Write-Host "       - Status: $($match.status)"
            Write-Host "       - Missing Person: $($match.missing_person_name)`n"
        }
    }
} catch {
    Write-Host "[ERROR] Failed to check matches: $_`n" -ForegroundColor Red
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. ADMIN STATS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "[7/7] Admin checking dashboard stats..." -ForegroundColor Yellow

try {
    $statsResp = Invoke-WebRequest -Uri "$BASE_URL/admin/stats" `
        -Method GET `
        -Headers @{"Authorization"="Bearer $ADMIN_TOKEN"} -UseBasicParsing -ErrorAction Stop

    $statsData = $statsResp.Content | ConvertFrom-Json

    Write-Host "[OK] Dashboard Statistics:" -ForegroundColor Green
    Write-Host "     Total Cases: $($statsData.cases)"
    Write-Host "     Active Cases: $($statsData.active_cases)"
    Write-Host "     Resolved Cases: $($statsData.resolved_cases)"
    Write-Host "     Total Sightings: $($statsData.sightings)"
    Write-Host "     Total Matches: $($statsData.matches)"
    Write-Host "     Volunteers: $($statsData.volunteers)`n"
} catch {
    Write-Host "[ERROR] Failed to get stats: $_`n" -ForegroundColor Red
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SUMMARY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "  MANUAL TEST COMPLETE" -ForegroundColor Cyan
Write-Host "===============================================`n" -ForegroundColor Cyan

Write-Host "Test Workflow Summary:" -ForegroundColor Yellow
Write-Host "  1. Created test image"
Write-Host "  2. Admin logged in"
Write-Host "  3. Test user registered (Priya Sharma)"
Write-Host "  4. Case filed (Rahul Verma, Mumbai)"
Write-Host "  5. Public sighting submitted"
Write-Host "  6. Matches checked"
Write-Host "  7. Admin stats retrieved`n"

Write-Host "Key Data:" -ForegroundColor Yellow
Write-Host "  Admin Token: $($ADMIN_TOKEN.Substring(0, 20))..."
Write-Host "  User Token: $($USER_TOKEN.Substring(0, 20))..."
Write-Host "  Case ID: $CASE_ID"
Write-Host "  Sighting ID: $SIGHTING_ID"
Write-Host "  Matches Found: $MATCHES_FOUND`n"

if ($MATCHES_FOUND -gt 0) {
    Write-Host "✅ FACE MATCHING SYSTEM WORKING!" -ForegroundColor Green
} else {
    Write-Host "⚠️  No matches found (face encoding may have failed or placeholder image)" -ForegroundColor Yellow
}

Write-Host "`nTest image at: $imagePath`n" -ForegroundColor Gray
