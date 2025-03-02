#!/bin/bash

# Configure metrics
configure_metrics() {
    local realm=$1
    local admin_user=$2
    local admin_password=$3
    local metrics_enabled=${4:-true}

    # Authenticate
    ./kcadm.sh config credentials \
        --server http://localhost:8080 \
        --realm master \
        --user "$admin_user" \
        --password "$admin_password"

    # Enable metrics endpoint
    ./kcadm.sh update realms/"$realm" \
        -s "metrics.enabled=$metrics_enabled" \
        -s "metrics.jvmEnabled=true" \
        -s "metrics.prefix=keycloak"
}

# Configure health checks
configure_health_checks() {
    local realm=$1
    local admin_user=$2
    local admin_password=$3
    local health_enabled=${4:-true}

    # Enable health endpoint
    ./kcadm.sh update realms/"$realm" \
        -s "health.enabled=$health_enabled" \
        -s "health.checkDatabaseInterval=60" \
        -s "health.checkMemoryInterval=60"
}

# Configure Prometheus endpoint
configure_prometheus() {
    local realm=$1
    local admin_user=$2
    local admin_password=$3
    local prometheus_user=$4
    local prometheus_password=$5

    # Create Prometheus client
    ./kcadm.sh create clients \
        -r "$realm" \
        -s clientId=prometheus \
        -s enabled=true \
        -s publicClient=false \
        -s standardFlowEnabled=false \
        -s serviceAccountsEnabled=true \
        -s directAccessGrantsEnabled=false

    # Get client ID
    client_id=$(./kcadm.sh get clients -r "$realm" -q clientId=prometheus --fields id | jq -r '.[0].id')

    # Create Prometheus user
    ./kcadm.sh create users \
        -r "$realm" \
        -s username="$prometheus_user" \
        -s enabled=true

    # Set password
    ./kcadm.sh set-password \
        -r "$realm" \
        --username "$prometheus_user" \
        --new-password "$prometheus_password"

    # Assign roles
    ./kcadm.sh add-roles \
        -r "$realm" \
        --uusername "$prometheus_user" \
        --cclientid prometheus \
        --rolename metrics-viewer
}
