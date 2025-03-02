#!/bin/bash

# Configure a client
configure_client() {
    local realm=$1
    local admin_user=$2
    local admin_password=$3
    local client_name=$4
    local client_type=$5

    # Authenticate
    ./kcadm.sh config credentials \
        --server http://localhost:8080 \
        --realm master \
        --user "$admin_user" \
        --password "$admin_password"

    # Create client
    local public_client="false"
    if [ "$client_type" = "public" ]; then
        public_client="true"
    fi

    ./kcadm.sh create clients \
        -r "$realm" \
        -s clientId="$client_name" \
        -s enabled=true \
        -s publicClient="$public_client" \
        -s standardFlowEnabled=true \
        -s implicitFlowEnabled=false \
        -s directAccessGrantsEnabled=true \
        -s serviceAccountsEnabled=false \
        -s 'redirectUris=["*"]' \
        -s 'webOrigins=["*"]' \
        -o 2>/dev/null || true

    # If confidential client, get client secret
    if [ "$client_type" = "confidential" ]; then
        client_id=$(./kcadm.sh get clients -r "$realm" -q clientId="$client_name" --fields id | jq -r '.[0].id')
        ./kcadm.sh get clients/"$client_id"/client-secret -r "$realm"
    fi
}

# Add protocol mapper
add_protocol_mapper() {
    local realm=$1
    local client_name=$2
    local mapper_name=$3
    local mapper_type=$4
    local protocol=${5:-"openid-connect"}
    
    # Get client ID
    client_id=$(./kcadm.sh get clients -r "$realm" -q clientId="$client_name" --fields id | jq -r '.[0].id')
    
    # Create protocol mapper
    ./kcadm.sh create clients/"$client_id"/protocol-mappers/models \
        -r "$realm" \
        -s name="$mapper_name" \
        -s protocol="$protocol" \
        -s protocolMapper="$mapper_type" \
        -s consentRequired=false \
        -s config="{\"userinfo.token.claim\":\"true\",\"id.token.claim\":\"true\",\"access.token.claim\":\"true\"}"
}

# Configure client scopes
configure_client_scope() {
    local realm=$1
    local client_name=$2
    local scope_name=$3
    local scope_type=${4:-"optional"}  # optional, default
    
    # Get client ID
    client_id=$(./kcadm.sh get clients -r "$realm" -q clientId="$client_name" --fields id | jq -r '.[0].id')
    
    # Add client scope
    ./kcadm.sh update clients/"$client_id"/default-client-scopes/"$scope_name" \
        -r "$realm" \
        -s "type=$scope_type"
}

# Configure service account
configure_service_account() {
    local realm=$1
    local client_name=$2
    local role_names=$3  # Comma-separated list of roles
    
    # Get client ID
    client_id=$(./kcadm.sh get clients -r "$realm" -q clientId="$client_name" --fields id | jq -r '.[0].id')
    
    # Enable service account
    ./kcadm.sh update clients/"$client_id" \
        -r "$realm" \
        -s serviceAccountsEnabled=true
    
    # Get service account user ID
    service_account_id=$(./kcadm.sh get clients/"$client_id"/service-account-user -r "$realm" --fields id | jq -r '.id')
    
    # Assign roles
    IFS=',' read -ra ROLES <<< "$role_names"
    for role in "${ROLES[@]}"; do
        ./kcadm.sh add-roles \
            -r "$realm" \
            --uusername service-account-"$client_name" \
            --rolename "$role"
    done
}
