# Test Environment Setup Script for Windows
$ErrorActionPreference = "Stop"

# Script root directory
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptRoot)

Write-Host "Setting up test environment..."

# Check Docker
Write-Host "Checking Docker status..."
$dockerStatus = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker is not running. Please start Docker Desktop."
    exit 1
}

# Start services
Write-Host "Starting Keycloak and PostgreSQL..."
Set-Location $projectRoot
docker-compose -f docker-compose.test.yml up -d

# Wait for services
Write-Host "Waiting for services to be healthy..."
$timeout = 300
$elapsed = 0
$interval = 5

while ($elapsed -lt $timeout) {
    $status = docker-compose -f docker-compose.test.yml ps --format "{{.Status}}"
    if ($status -match "healthy") {
        Write-Host "Services are ready!"
        break
    }
    Write-Host "Waiting for services... ($($timeout - $elapsed) seconds remaining)"
    Start-Sleep -Seconds $interval
    $elapsed += $interval
}

if ($elapsed -ge $timeout) {
    Write-Error "Timeout waiting for services"
    exit 1
}

# Create test directories
Write-Host "Creating test directories..."
$testDirs = @(
    "tests/data/realms",
    "tests/data/clients",
    "tests/data/users"
)

foreach ($dir in $testDirs) {
    $path = Join-Path $projectRoot $dir
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
        Write-Host "Created directory: $dir"
    }
}

# Copy test config
Write-Host "Copying test configuration..."
$sourceConfig = Join-Path $projectRoot "tests/config/test_config.yml"
$targetConfig = Join-Path $projectRoot "tests/data/test_config.yml"
Copy-Item -Path $sourceConfig -Destination $targetConfig -Force

Write-Host "Test environment setup completed!"

# Display service status
Write-Host "`nService Status:"
docker-compose -f docker-compose.test.yml ps
