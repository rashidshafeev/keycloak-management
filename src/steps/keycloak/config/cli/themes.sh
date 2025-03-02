#!/bin/bash

# Configure realm theme settings
configure_realm_themes() {
    local realm=$1
    local admin_user=$2
    local admin_password=$3
    local login_theme=${4:-"keycloak"}
    local account_theme=${5:-"keycloak"}
    local admin_theme=${6:-"keycloak"}
    local email_theme=${7:-"keycloak"}

    # Authenticate
    ./kcadm.sh config credentials \
        --server http://localhost:8080 \
        --realm master \
        --user "$admin_user" \
        --password "$admin_password"

    # Update realm theme settings
    ./kcadm.sh update realms/"$realm" \
        -s loginTheme="$login_theme" \
        -s accountTheme="$account_theme" \
        -s adminTheme="$admin_theme" \
        -s emailTheme="$email_theme"
}

# Upload custom theme
upload_custom_theme() {
    local realm=$1
    local theme_path=$2
    local theme_name=$3

    # Copy theme to Keycloak themes directory
    docker cp "$theme_path" keycloak:/opt/keycloak/themes/"$theme_name"

    # Restart Keycloak to pick up new theme
    docker restart keycloak
}

# Configure internationalization
configure_internationalization() {
    local realm=$1
    local admin_user=$2
    local admin_password=$3
    local supported_locales=$4  # Comma-separated list
    local default_locale=${5:-"en"}

    # Update realm internationalization settings
    ./kcadm.sh update realms/"$realm" \
        -s "internationalizationEnabled=true" \
        -s "supportedLocales=[${supported_locales}]" \
        -s "defaultLocale=$default_locale"
}
