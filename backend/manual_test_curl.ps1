#!/usr/bin/env powershell
# Manual Testing Script - Using curl.exe for file uploads
# This works on Windows 10 PowerShell without needing -Form parameter

Write-Host "`n===============================================" -ForegroundColor Cyan
Write-Host "  MANUAL API TESTING - MISSING PERSON TRACKER" -ForegroundColor Cyan
Write-Host "===============================================`n" -ForegroundColor Cyan

$BASE_URL = "http://localhost:8000"
$imageDir = "$PSScriptRoot\test_images"

# Create directory for test images
if (!(Test-Path $imageDir)) {
    New-Item -ItemType Directory -Path $imageDir -Force | Out-Null
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. CREATE TEST IMAGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "[1/7] Creating test image..." -ForegroundColor Yellow

$imagePath = "$imageDir\test_person.png"

# Create a simple 1x1 PNG
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
Write-Host "[OK] Test image created`n" -ForegroundColor Green

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. GET ADMIN TOKEN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "[2/7] Getting admin token..." -ForegroundColor Yellow

$adminJson = @{
    email = "admin@example.com"
    password = "Admin@1234"
} | ConvertTo-Json | Out-String

$adminResp = (curl.exe -s -X POST "$BASE_URL/auth/login" `
    -H "Content-Type: application/json" `
    -d $adminJson | ConvertFrom-Json)

$ADMIN_TOKEN = $adminResp.token
Write-Host "[OK] Admin token acquired`n" -ForegroundColor Green

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. REGISTER TEST USER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "[3/7] Registering test user (Priya Sharma)..." -ForegroundColor Yellow

$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$uniqueEmail = "priya.test+$timestamp@test.com"

$registerJson = @{
    name = "Priya Sharma"
    email = $uniqueEmail
    password = "Test@1234"
    phone = "9876543210"
} | ConvertTo-Json | Out-String

$userResp = (curl.exe -s -X POST "$BASE_URL/auth/register" `
    -H "Content-Type: application/json" `
    -d $registerJson | ConvertFrom-Json)

$USER_TOKEN = $userResp.token
$USER_ID = $userResp.id

Write-Host "[OK] User registered:" -ForegroundColor Green
Write-Host "     Email: $uniqueEmail"
Write-Host "     User ID: $USER_ID`n"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. FILE A CASE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "[4/7] Filing missing person case (Rahul Verma)..." -ForegroundColor Yellow

$caseResp = (curl.exe -s -X POST "$BASE_URL/cases" `
    -H "Authorization: Bearer $USER_TOKEN" `
    -F "full_name=Rahul Verma" `
    -F "age=28" `
    -F "gender=Male" `
    -F "last_seen_date=2026-04-05" `
    -F "last_seen_city=Mumbai" `
    -F "last_seen_state=Maharashtra" `
    -F "last_seen_address=Marine Drive" `
    -F "description=Wearing red shirt" `
    -F "police_dispatch_mode=manual" `
    -F "photo=@$imagePath" | ConvertFrom-Json)

$CASE_ID = $caseResp.case_id
Write-Host "[OK] Case filed:" -ForegroundColor Green
Write-Host "     Case ID: $CASE_ID"
Write-Host "     Missing Person: Rahul Verma`n"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. SUBMIT PUBLIC SIGHTING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "[5/7] Submitting public sighting (same photo)..." -ForegroundColor Yellow

$sightingResp = (curl.exe -s -X POST "$BASE_URL/sightings" `
    -F "sighting_lat=19.0760" `
    -F "sighting_lng=72.8777" `
    -F "reporter_name=Witness" `
    -F "reporter_phone=9988776655" `
    -F "photo=@$imagePath" | ConvertFrom-Json)

$SIGHTING_ID = $sightingResp.sighting_id
$MATCHES_FOUND = $sightingResp.matches_found

Write-Host "[OK] Sighting reported:" -ForegroundColor Green
Write-Host "     Sighting ID: $SIGHTING_ID"
Write-Host "     Location: Mumbai (19.0760, 72.8777)"
Write-Host "     Matches Found: $MATCHES_FOUND`n"

if ($MATCHES_FOUND -gt 0) {
    Write-Host "     >>> MATCH DETECTED! <<<" -ForegroundColor Cyan
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. ADMIN CHECKS MATCHES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "[6/7] Admin checking matches..." -ForegroundColor Yellow

$matchesResp = (curl.exe -s -X GET "$BASE_URL/matches" `
    -H "Authorization: Bearer $ADMIN_TOKEN" | ConvertFrom-Json)

$TOTAL_MATCHES = $matchesResp.total

Write-Host "[OK] Matches retrieved:" -ForegroundColor Green
Write-Host "     Total Matches: $TOTAL_MATCHES`n"

if ($matchesResp.matches.Count -gt 0) {
    foreach ($match in $matchesResp.matches) {
        Write-Host "     Match #$($match.id):" -ForegroundColor Cyan
        Write-Host "       - Case: $($match.case_id)"
        Write-Host "       - Confidence: $($match.confidence) ($($match.label))"
        Write-Host "       - Status: $($match.status)"
        Write-Host "       - Missing Person: $($match.missing_person_name)`n"
    }
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. ADMIN STATS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write-Host "[7/7] Admin checking dashboard stats..." -ForegroundColor Yellow

$statsResp = (curl.exe -s -X GET "$BASE_URL/admin/stats" `
    -H "Authorization: Bearer $ADMIN_TOKEN" | ConvertFrom-Json)

Write-Host "[OK] Dashboard Statistics:" -ForegroundColor Green
Write-Host "     Total Cases: $($statsResp.cases)"
Write-Host "     Active Cases: $($statsResp.active_cases)"
Write-Host "     Resolved Cases: $($statsResp.resolved_cases)"
Write-Host "     Total Sightings: $($statsResp.sightings)"
Write-Host "     Total Matches: $($statsResp.matches)"
Write-Host "     Volunteers: $($statsResp.volunteers)`n"

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
