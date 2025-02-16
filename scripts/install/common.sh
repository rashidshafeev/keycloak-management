#!/bin/bash

# Base paths
INSTALL_DIR="${INSTALL_DIR:-/opt/fawz/keycloak}"
VENV_DIR="${VENV_DIR:-${INSTALL_DIR}/venv}"
LOG_FILE="${LOG_FILE:-/var/log/keycloak-install.log}"
BACKUP_DIR="${BACKUP_DIR:-/opt/fawz/backup}"
STATE_FILE="${STATE_FILE:-/opt/fawz/.install_state}"

# Repository settings
REPO_URL="${REPO_URL:-https://git.rashidshafeev.ru/rashidshafeev/keycloak-management.git}"

# Default ports
HTTP_PORT="${HTTP_PORT:-80}"
HTTPS_PORT="${HTTPS_PORT:-443}"
KEYCLOAK_PORT="${KEYCLOAK_PORT:-8443}"
GRAFANA_PORT="${GRAFANA_PORT:-3000}"
PROMETHEUS_PORT="${PROMETHEUS_PORT:-9090}"
NODE_EXPORTER_PORT="${NODE_EXPORTER_PORT:-9100}"
DOCKER_METRICS_PORT="${DOCKER_METRICS_PORT:-9323}"

# Default credentials (will be overridden with secure values)
KEYCLOAK_ADMIN="${KEYCLOAK_ADMIN:-admin}"
KEYCLOAK_ADMIN_PASSWORD="${KEYCLOAK_ADMIN_PASSWORD:-admin}"
KEYCLOAK_DB_USER="${KEYCLOAK_DB_USER:-keycloak}"
KEYCLOAK_DB_PASSWORD="${KEYCLOAK_DB_PASSWORD:-keycloak}"
KEYCLOAK_DB_NAME="${KEYCLOAK_DB_NAME:-keycloak}"
KEYCLOAK_DB_HOST="${KEYCLOAK_DB_HOST:-postgres}"

# Docker settings
DOCKER_REGISTRY="${DOCKER_REGISTRY:-docker.io}"
KEYCLOAK_VERSION="${KEYCLOAK_VERSION:-latest}"
POSTGRES_VERSION="${POSTGRES_VERSION:-latest}"

# SSL settings
SSL_CERT_PATH="${SSL_CERT_PATH:-/etc/letsencrypt/live/\${KEYCLOAK_DOMAIN}/fullchain.pem}"
SSL_KEY_PATH="${SSL_KEY_PATH:-/etc/letsencrypt/live/\${KEYCLOAK_DOMAIN}/privkey.pem}"

# Prometheus settings
PROMETHEUS_SCRAPE_INTERVAL="${PROMETHEUS_SCRAPE_INTERVAL:-15s}"
PROMETHEUS_EVAL_INTERVAL="${PROMETHEUS_EVAL_INTERVAL:-15s}"
PROMETHEUS_RETENTION_TIME="${PROMETHEUS_RETENTION_TIME:-15d}"
PROMETHEUS_STORAGE_SIZE="${PROMETHEUS_STORAGE_SIZE:-50GB}"
PROMETHEUS_DATA_DIR="${PROMETHEUS_DATA_DIR:-/var/lib/prometheus}"

# Grafana settings
GRAFANA_ADMIN_USER="${GRAFANA_ADMIN_USER:-admin}"
GRAFANA_ADMIN_PASSWORD="${GRAFANA_ADMIN_PASSWORD:-admin}"

# SMTP settings
GRAFANA_SMTP_ENABLED="${GRAFANA_SMTP_ENABLED:-true}"
GRAFANA_SMTP_HOST="${GRAFANA_SMTP_HOST:-smtp.gmail.com}"
GRAFANA_SMTP_PORT="${GRAFANA_SMTP_PORT:-587}"
GRAFANA_SMTP_USER="${GRAFANA_SMTP_USER:-alerts@example.com}"
GRAFANA_SMTP_PASSWORD="${GRAFANA_SMTP_PASSWORD:-}"
GRAFANA_SMTP_FROM="${GRAFANA_SMTP_FROM:-alerts@example.com}"

# Alert settings
GRAFANA_ALERT_EMAIL="${GRAFANA_ALERT_EMAIL:-admin@example.com}"
GRAFANA_SLACK_WEBHOOK_URL="${GRAFANA_SLACK_WEBHOOK_URL:-}"
GRAFANA_SLACK_CHANNEL="${GRAFANA_SLACK_CHANNEL:-#alerts}"

# Wazuh settings
WAZUH_MANAGER_IP="${WAZUH_MANAGER_IP:-localhost}"
WAZUH_REGISTRATION_PASSWORD="${WAZUH_REGISTRATION_PASSWORD:-wazuh}"
WAZUH_AGENT_NAME="${WAZUH_AGENT_NAME:-keycloak-agent}"

# Firewall settings
FIREWALL_MAX_BACKUPS="${FIREWALL_MAX_BACKUPS:-5}"
FIREWALL_ALLOWED_PORTS="${FIREWALL_ALLOWED_PORTS:-22,80,443,8080,8443,3000,9090,9100,9323}"
FIREWALL_ADMIN_IPS="${FIREWALL_ADMIN_IPS:-127.0.0.1}"

# Backup settings
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

# Logging settings
LOG_LEVEL="${LOG_LEVEL:-INFO}"
LOG_FORMAT="${LOG_FORMAT:-json}"
LOG_MAX_SIZE="${LOG_MAX_SIZE:-100MB}"
LOG_MAX_FILES="${LOG_MAX_FILES:-10}"

# Keycloak domain and admin settings
HOSTNAME=$(hostname -f)
KEYCLOAK_DOMAIN="${KEYCLOAK_DOMAIN:-${HOSTNAME}}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@${HOSTNAME}}"

# Initialize state tracking
declare -A completed_steps

# Logging setup
setup_logging() {
    mkdir -p "$(dirname "$LOG_FILE")"
    exec 1> >(tee -a "$LOG_FILE")
    exec 2> >(tee -a "$LOG_FILE" >&2)
    echo "Starting installation at $(date)"
}

# State management
save_state() {
    local step=$1
    completed_steps[$step]=1
    mkdir -p "$(dirname "$STATE_FILE")"
    printf "%s\n" "${!completed_steps[@]}" > "$STATE_FILE"
}

load_state() {
    if [[ -f "$STATE_FILE" ]]; then
        while IFS= read -r step; do
            completed_steps[$step]=1
        done < "$STATE_FILE"
    fi
}

# Error handling
handle_error() {
    local exit_code=$1
    local error_msg=$2
    local step_name=$3
    
    echo "Error in step ${step_name}: ${error_msg}"
    echo "Exit code: ${exit_code}"
    
    # Log error details
    {
        echo "=== Error Details ==="
        echo "Timestamp: $(date)"
        echo "Step: ${step_name}"
        echo "Error Message: ${error_msg}"
        echo "Exit Code: ${exit_code}"
        echo "===================="
    } >> "$LOG_FILE"
    
    exit "${exit_code}"
}

clone_repository() {
    if [[ -z "${completed_steps[repository]}" ]]; then
        echo "Setting up repository..."
        
        # Create installation directory
        mkdir -p "${INSTALL_DIR}"
        
        # Clone repository
        if [ ! -d "${INSTALL_DIR}/.git" ]; then
            if ! git clone "${REPO_URL}" "${INSTALL_DIR}"; then
                handle_error $? "Failed to clone repository" "clone_repository"
            fi
            
            # Configure git to trust this directory
            if ! git config --global --get-all safe.directory | grep -q "^${INSTALL_DIR}\$"; then
                echo "Configuring git to trust ${INSTALL_DIR}..."
                git config --global --add safe.directory "${INSTALL_DIR}"
            fi
        else
            echo "Repository exists, updating..."
            cd "${INSTALL_DIR}"
            git pull
        fi
        
        save_state "repository"
    else
        echo "Repository already set up, skipping..."
    fi
}

reset_installation() {
    echo "Performing reset..."
    
    # Stop and remove Docker containers
    if [ -f "${INSTALL_DIR}/docker-compose.yml" ]; then
        echo "Stopping Docker containers..."
        cd "${INSTALL_DIR}" && docker-compose down -v || true
    fi
    
    # Stop all containers with 'keycloak' in their name
    echo "Stopping any remaining Keycloak containers..."
    docker ps -aq --filter "name=keycloak" | xargs -r docker rm -f || true
    docker ps -aq --filter "name=postgres" | xargs -r docker rm -f || true
    
    # Remove all volumes
    echo "Removing Docker volumes..."
    docker volume ls -q --filter "name=keycloak" | xargs -r docker volume rm || true
    
    # Clean up Docker system
    echo "Cleaning up Docker system..."
    docker system prune -f || true

    # Remove all directories and files
    echo "Removing installation files..."
    rm -rf "${INSTALL_DIR}" 2>/dev/null || true
    rm -rf "/opt/fawz/backup" 2>/dev/null || true
    rm -f /usr/local/bin/keycloak-deploy 2>/dev/null || true
    rm -f "${STATE_FILE}" 2>/dev/null || true

    # Reset state
    completed_steps=()
    
    echo "Reset completed successfully."
}

export -f handle_error
export -f save_state
export -f load_state
export -f clone_repository
export -f reset_installation
export -f setup_logging
export completed_steps
export INSTALL_DIR
export VENV_DIR
export LOG_FILE
export BACKUP_DIR
export STATE_FILE
export REPO_URL
export HTTP_PORT
export HTTPS_PORT
export KEYCLOAK_PORT
export GRAFANA_PORT
export PROMETHEUS_PORT
export NODE_EXPORTER_PORT
export DOCKER_METRICS_PORT
export KEYCLOAK_ADMIN
export KEYCLOAK_ADMIN_PASSWORD
export KEYCLOAK_DB_USER
export KEYCLOAK_DB_PASSWORD
export KEYCLOAK_DB_NAME
export KEYCLOAK_DB_HOST
export DOCKER_REGISTRY
export KEYCLOAK_VERSION
export POSTGRES_VERSION
export SSL_CERT_PATH
export SSL_KEY_PATH
export PROMETHEUS_SCRAPE_INTERVAL
export PROMETHEUS_EVAL_INTERVAL
export PROMETHEUS_RETENTION_TIME
export PROMETHEUS_STORAGE_SIZE
export PROMETHEUS_DATA_DIR
export GRAFANA_ADMIN_USER
export GRAFANA_ADMIN_PASSWORD
export GRAFANA_SMTP_ENABLED
export GRAFANA_SMTP_HOST
export GRAFANA_SMTP_PORT
export GRAFANA_SMTP_USER
export GRAFANA_SMTP_PASSWORD
export GRAFANA_SMTP_FROM
export GRAFANA_ALERT_EMAIL
export GRAFANA_SLACK_WEBHOOK_URL
export GRAFANA_SLACK_CHANNEL
export WAZUH_MANAGER_IP
export WAZUH_REGISTRATION_PASSWORD
export WAZUH_AGENT_NAME
export FIREWALL_MAX_BACKUPS
export FIREWALL_ALLOWED_PORTS
export FIREWALL_ADMIN_IPS
export BACKUP_RETENTION_DAYS
export LOG_LEVEL
export LOG_FORMAT
export LOG_MAX_SIZE
export LOG_MAX_FILES
export KEYCLOAK_DOMAIN
export ADMIN_EMAIL
