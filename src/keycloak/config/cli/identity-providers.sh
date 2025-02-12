#!/bin/bash

# Configure identity provider
configure_identity_provider() {
    local realm=$1
    local admin_user=$2
    local admin_password=$3
    local provider_alias=$4
    local provider_id=$5
    local display_name=$6

    # Authenticate
    ./kcadm.sh config credentials \
        --server http://localhost:8080 \
        --realm master \
        --user "$admin_user" \
        --password "$admin_password"

    # Create identity provider
    ./kcadm.sh create identity-provider/instances \
        -r "$realm" \
        -s alias="$provider_alias" \
        -s providerId="$provider_id" \
        -s enabled=true \
        -s displayName="$display_name" \
        -s storeToken=false \
        -s addReadTokenRoleOnCreate=false \
        -s trustEmail=false \
        -s linkOnly=false \
        -o 2>/dev/null || true
}

# Configure OIDC provider
configure_oidc_provider() {
    local realm=$1
    local provider_alias=$2
    local client_id=$3
    local client_secret=$4
    local authorization_url=$5
    local token_url=$6

    ./kcadm.sh update identity-provider/instances/"$provider_alias" \
        -r "$realm" \
        -s "config.clientId=$client_id" \
        -s "config.clientSecret=$client_secret" \
        -s "config.authorizationUrl=$authorization_url" \
        -s "config.tokenUrl=$token_url" \
        -s "config.defaultScope=openid profile email" \
        -s "config.useJwksUrl=true" \
        -s "config.validateSignature=true"
}

# Configure SAML provider
configure_saml_provider() {
    local realm=$1
    local provider_alias=$2
    local entity_id=$3
    local sso_url=$4
    local certificate=$5

    ./kcadm.sh update identity-provider/instances/"$provider_alias" \
        -r "$realm" \
        -s "config.entityId=$entity_id" \
        -s "config.singleSignOnServiceUrl=$sso_url" \
        -s "config.signatureAlgorithm=RSA_SHA256" \
        -s "config.xmlSigKeyInfoKeyNameTransformer=KEY_ID" \
        -s "config.signingCertificate=$certificate" \
        -s "config.validateSignature=true"
}

# Configure social provider
configure_social_provider() {
    local realm=$1
    local provider_alias=$2
    local provider_id=$3
    local client_id=$4
    local client_secret=$5

    configure_identity_provider "$realm" "$admin_user" "$admin_password" \
        "$provider_alias" "$provider_id" "$provider_id"

    ./kcadm.sh update identity-provider/instances/"$provider_alias" \
        -r "$realm" \
        -s "config.clientId=$client_id" \
        -s "config.clientSecret=$client_secret"
}
