#!/bin/bash

# Configure SMTP settings
configure_smtp() {
    local realm=$1
    local admin_user=$2
    local admin_password=$3
    local host=$4
    local port=$5
    local from_address=$6
    local username=${7:-""}
    local password=${8:-""}
    local ssl=${9:-false}
    local starttls=${10:-true}
    local auth=${11:-true}

    # Authenticate
    ./kcadm.sh config credentials \
        --server http://localhost:8080 \
        --realm master \
        --user "$admin_user" \
        --password "$admin_password"

    # Configure SMTP settings
    ./kcadm.sh update realms/"$realm" \
        -s "smtpServer.host=$host" \
        -s "smtpServer.port=$port" \
        -s "smtpServer.from=$from_address" \
        -s "smtpServer.ssl=$ssl" \
        -s "smtpServer.starttls=$starttls" \
        -s "smtpServer.auth=$auth"

    # Add credentials if authentication is enabled
    if [ "$auth" = true ] && [ -n "$username" ]; then
        ./kcadm.sh update realms/"$realm" \
            -s "smtpServer.user=$username" \
            -s "smtpServer.password=$password"
    fi
}

# Test SMTP configuration
test_smtp_config() {
    local realm=$1
    local admin_user=$2
    local admin_password=$3
    local test_address=$4

    # Send test email
    ./kcadm.sh create test/smtp \
        -r "$realm" \
        -s recipient="$test_address"
}
