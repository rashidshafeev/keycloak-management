#!/bin/bash

source "./scripts/install/common.sh"

generate_secure_password() {
    openssl rand -base64 12
}

prompt_for_variables() {
    # Get system hostname for suggestions
    local HOSTNAME=$(hostname -f)
    
    # Domain
    if [ -z "${KEYCLOAK_DOMAIN}" ]; then
        read -p "Enter domain name [${HOSTNAME}]: " input_domain
        KEYCLOAK_DOMAIN=${input_domain:-$HOSTNAME}
        export KEYCLOAK_DOMAIN
    fi
    
    # Admin email
    if [ -z "${ADMIN_EMAIL}" ]; then
        read -p "Enter admin email [admin@${HOSTNAME}]: " input_email
        ADMIN_EMAIL=${input_email:-admin@$HOSTNAME}
        export ADMIN_EMAIL
    fi
    
    # SMTP settings
    if [ -z "${GRAFANA_SMTP_HOST}" ]; then
        read -p "Enter SMTP host [smtp.gmail.com]: " input_smtp_host
        GRAFANA_SMTP_HOST=${input_smtp_host:-smtp.gmail.com}
        export GRAFANA_SMTP_HOST
    fi
    
    if [ -z "${GRAFANA_SMTP_PORT}" ]; then
        read -p "Enter SMTP port [587]: " input_smtp_port
        GRAFANA_SMTP_PORT=${input_smtp_port:-587}
        export GRAFANA_SMTP_PORT
    fi
}

check_required_variables() {
    local missing_vars=()
    
    # Check required variables
    if [ -z "${KEYCLOAK_DOMAIN}" ]; then
        missing_vars+=("KEYCLOAK_DOMAIN")
    fi
    
    if [ -z "${ADMIN_EMAIL}" ]; then
        missing_vars+=("ADMIN_EMAIL")
    fi
    
    # If any variables are missing, prompt for them
    if [ ${#missing_vars[@]} -gt 0 ]; then
        echo "Missing required variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        prompt_for_variables
    fi
}

setup_environment() {
    if [[ -z "${completed_steps[environment]}" ]]; then
        echo "Setting up environment..."
        
        # Check and prompt for required variables
        check_required_variables
        
        # Generate passwords if not set
        if [ -z "${KEYCLOAK_ADMIN_PASSWORD}" ]; then
            KEYCLOAK_ADMIN_PASSWORD=$(generate_secure_password)
            export KEYCLOAK_ADMIN_PASSWORD
        fi
        
        if [ -z "${KEYCLOAK_DB_PASSWORD}" ]; then
            KEYCLOAK_DB_PASSWORD=$(generate_secure_password)
            export KEYCLOAK_DB_PASSWORD
        fi
        
        if [ -z "${GRAFANA_ADMIN_PASSWORD}" ]; then
            GRAFANA_ADMIN_PASSWORD=$(generate_secure_password)
            export GRAFANA_ADMIN_PASSWORD
        fi
        
        # Set default values for optional variables
        : ${KEYCLOAK_ADMIN:=admin}
        : ${KEYCLOAK_DB_USER:=keycloak}
        : ${KEYCLOAK_DB_NAME:=keycloak}
        : ${KEYCLOAK_DB_HOST:=postgres}
        : ${DOCKER_REGISTRY:=docker.io}
        : ${KEYCLOAK_VERSION:=latest}
        : ${POSTGRES_VERSION:=latest}
        : ${PROMETHEUS_SCRAPE_INTERVAL:=15s}
        : ${PROMETHEUS_EVAL_INTERVAL:=15s}
        : ${PROMETHEUS_RETENTION_TIME:=15d}
        : ${PROMETHEUS_STORAGE_SIZE:=5Gi}
        : ${GRAFANA_ADMIN_USER:=admin}
        : ${GRAFANA_SMTP_ENABLED:=false}
        : ${GRAFANA_SMTP_USER:=}
        : ${GRAFANA_SMTP_PASSWORD:=}
        : ${GRAFANA_SMTP_FROM:=}
        : ${GRAFANA_ALERT_EMAIL:=}
        : ${GRAFANA_SLACK_WEBHOOK_URL:=}
        : ${GRAFANA_SLACK_CHANNEL:=}
        : ${WAZUH_MANAGER_IP:=}
        : ${WAZUH_REGISTRATION_PASSWORD:=}
        : ${WAZUH_AGENT_NAME:=keycloak}
        : ${FIREWALL_MAX_BACKUPS:=5}
        : ${FIREWALL_ALLOWED_PORTS:=}
        : ${FIREWALL_ADMIN_IPS:=}
        : ${BACKUP_RETENTION_DAYS:=7}
        : ${LOG_LEVEL:=info}
        : ${LOG_FORMAT:=text}
        : ${LOG_MAX_SIZE:=10m}
        : ${LOG_MAX_FILES:=5}
        
        # Export all variables
        export KEYCLOAK_ADMIN
        export KEYCLOAK_DB_USER
        export KEYCLOAK_DB_NAME
        export KEYCLOAK_DB_HOST
        export DOCKER_REGISTRY
        export KEYCLOAK_VERSION
        export POSTGRES_VERSION
        export PROMETHEUS_SCRAPE_INTERVAL
        export PROMETHEUS_EVAL_INTERVAL
        export PROMETHEUS_RETENTION_TIME
        export PROMETHEUS_STORAGE_SIZE
        export GRAFANA_ADMIN_USER
        export GRAFANA_SMTP_ENABLED
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
        
        save_state "environment"
    else
        echo "Environment already set up, skipping..."
    fi
}

export -f generate_secure_password
export -f prompt_for_variables
export -f check_required_variables
export -f setup_environment
