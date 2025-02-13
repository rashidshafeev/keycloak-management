# Keycloak Management Script for Windows
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('authentication', 'clients', 'events', 'identity-providers', 'monitoring', 'realm', 'roles', 'smtp', 'themes')]
    [string]$Command
)

# Script root directory
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptRoot)

# Load environment variables
$envFile = Join-Path $projectRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2])
        }
    }
}

# Default values if not in .env
if (-not $env:KEYCLOAK_URL) { $env:KEYCLOAK_URL = "http://localhost:8080" }
if (-not $env:KEYCLOAK_ADMIN) { $env:KEYCLOAK_ADMIN = "admin" }
if (-not $env:KEYCLOAK_ADMIN_PASSWORD) { $env:KEYCLOAK_ADMIN_PASSWORD = "admin" }

# Check Docker
Write-Host "Checking Docker status..."
$dockerStatus = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker is not running. Please start Docker Desktop."
    exit 1
}

# Check Keycloak
Write-Host "Checking Keycloak status..."
$keycloakRunning = docker ps --filter "name=keycloak" --format "{{.Status}}" | Select-String "Up"
if (-not $keycloakRunning) {
    Write-Host "Starting Keycloak..."
    Set-Location $projectRoot
    docker-compose up -d
    Write-Host "Waiting for Keycloak to start..."
    Start-Sleep -Seconds 15
}

# Script mapping
$scripts = @{
    'authentication' = 'src/keycloak/config/cli/authentication.sh'
    'clients' = 'src/keycloak/config/cli/clients.sh'
    'events' = 'src/keycloak/config/cli/events.sh'
    'identity-providers' = 'src/keycloak/config/cli/identity-providers.sh'
    'monitoring' = 'src/keycloak/config/cli/monitoring.sh'
    'realm' = 'src/keycloak/config/cli/realm.sh'
    'roles' = 'src/keycloak/config/cli/roles.sh'
    'smtp' = 'src/keycloak/config/cli/smtp.sh'
    'themes' = 'src/keycloak/config/cli/themes.sh'
}

# Find Git Bash
$gitBashPaths = @(
    "D:\Program Files\Git\usr\bin\bash.exe",
    "C:\Program Files\Git\usr\bin\bash.exe",
    "C:\Program Files (x86)\Git\usr\bin\bash.exe"
)

$gitBash = $null
foreach ($path in $gitBashPaths) {
    if (Test-Path $path) {
        $gitBash = $path
        break
    }
}

if (-not $gitBash) {
    Write-Error "Git Bash not found. Please install Git for Windows."
    exit 1
}

# Run the script
$scriptPath = Join-Path $projectRoot $scripts[$Command]
if (-not (Test-Path $scriptPath)) {
    Write-Error "Script not found: $scriptPath"
    exit 1
}

Write-Host "Running $Command configuration..."
$scriptDir = Split-Path -Parent $scriptPath
Set-Location $scriptDir

# Make script executable
& $gitBash -c "chmod +x $(Split-Path -Leaf $scriptPath)"

# Run the script
& $gitBash -c "./$(Split-Path -Leaf $scriptPath)"

if ($LASTEXITCODE -ne 0) {
    Write-Error "Command failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host "Configuration completed successfully!"
