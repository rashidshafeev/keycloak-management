#!/bin/bash

# Configure a realm
configure_realm() {
    local realm=$1
    local admin_user=$2
    local admin_password=$3

    # Authenticate
    ./kcadm.sh config credentials \
        --server http://localhost:8080 \
        --realm master \
        --user "$admin_user" \
        --password "$admin_password"

    # Create realm if it doesn't exist
    ./kcadm.sh create realms \
        -s realm="$realm" \
        -s enabled=true \
        -s displayName="$realm" \
        -s sslRequired=EXTERNAL \
        -s registrationAllowed=false \
        -s loginWithEmailAllowed=true \
        -s duplicateEmailsAllowed=false \
        -s resetPasswordAllowed=true \
        -s editUsernameAllowed=false \
        -s bruteForceProtected=true \
        -o 2>/dev/null || true

    # Update realm settings
    ./kcadm.sh update realms/"$realm" \
        -s "defaultSignatureAlgorithm=RS256" \
        -s "revokeRefreshToken=true" \
        -s "refreshTokenMaxReuse=0" \
        -s "ssoSessionIdleTimeout=1800" \
        -s "ssoSessionMaxLifespan=36000" \
        -s "accessTokenLifespan=300" \
        -s "accessTokenLifespanForImplicitFlow=900" \
        -s "offlineSessionIdleTimeout=2592000"
}
