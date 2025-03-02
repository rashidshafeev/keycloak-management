#!/bin/bash

# Configure a role
configure_role() {
    local realm=$1
    local admin_user=$2
    local admin_password=$3
    local role_name=$4
    local role_description=$5

    # Authenticate
    ./kcadm.sh config credentials \
        --server http://localhost:8080 \
        --realm master \
        --user "$admin_user" \
        --password "$admin_password"

    # Create role
    ./kcadm.sh create roles \
        -r "$realm" \
        -s name="$role_name" \
        -s description="$role_description" \
        -o 2>/dev/null || true

    # If this is the default role, set it
    if [ "$role_name" = "user" ]; then
        ./kcadm.sh update realms/"$realm" \
            -s 'defaultRoles=["user"]'
    fi
}

# Create composite role
create_composite_role() {
    local realm=$1
    local composite_role=$2
    local sub_roles=$3  # Comma-separated list of role names
    
    # Create the composite role first
    ./kcadm.sh create roles \
        -r "$realm" \
        -s name="$composite_role" \
        -s composite=true \
        -o 2>/dev/null || true
    
    # Add sub-roles
    IFS=',' read -ra ROLES <<< "$sub_roles"
    for role in "${ROLES[@]}"; do
        ./kcadm.sh add-roles \
            -r "$realm" \
            --rname "$composite_role" \
            --rolename "$role"
    done
}

# Create client role
create_client_role() {
    local realm=$1
    local client_name=$2
    local role_name=$3
    local role_description=$4
    
    # Get client ID
    client_id=$(./kcadm.sh get clients -r "$realm" -q clientId="$client_name" --fields id | jq -r '.[0].id')
    
    # Create client role
    ./kcadm.sh create clients/"$client_id"/roles \
        -r "$realm" \
        -s name="$role_name" \
        -s description="$role_description" \
        -o 2>/dev/null || true
}

# Assign role to group
assign_role_to_group() {
    local realm=$1
    local group_name=$2
    local role_names=$3  # Comma-separated list of roles
    
    # Get group ID
    group_id=$(./kcadm.sh get groups -r "$realm" -q name="$group_name" --fields id | jq -r '.[0].id')
    
    # Assign roles
    IFS=',' read -ra ROLES <<< "$role_names"
    for role in "${ROLES[@]}"; do
        ./kcadm.sh add-roles \
            -r "$realm" \
            --gid "$group_id" \
            --rolename "$role"
    done
}
