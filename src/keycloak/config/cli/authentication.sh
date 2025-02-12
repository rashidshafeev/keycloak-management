#!/bin/bash

# Configure authentication flow
configure_auth_flow() {
    local realm=$1
    local admin_user=$2
    local admin_password=$3
    local flow_alias=$4
    local flow_type=${5:-"basic-flow"}

    # Authenticate
    ./kcadm.sh config credentials \
        --server http://localhost:8080 \
        --realm master \
        --user "$admin_user" \
        --password "$admin_password"

    # Create authentication flow
    ./kcadm.sh create authentication/flows \
        -r "$realm" \
        -s alias="$flow_alias" \
        -s providerId="$flow_type" \
        -s topLevel=true \
        -s builtIn=false \
        -o 2>/dev/null || true

    # Get flow ID
    flow_id=$(./kcadm.sh get authentication/flows -r "$realm" -q "alias=$flow_alias" --fields id | jq -r '.[0].id')
}

# Add execution to flow
add_flow_execution() {
    local realm=$1
    local flow_alias=$2
    local provider=$3
    local requirement=${4:-"REQUIRED"}
    local priority=${5:-10}

    ./kcadm.sh create authentication/flows/"$flow_alias"/executions/execution \
        -r "$realm" \
        -s provider="$provider" \
        -s requirement="$requirement" \
        -s priority="$priority"
}

# Configure required action
configure_required_action() {
    local realm=$1
    local action_alias=$2
    local action_name=$3
    local enabled=${4:-true}
    local default_action=${5:-false}

    ./kcadm.sh update authentication/required-actions/"$action_alias" \
        -r "$realm" \
        -s alias="$action_alias" \
        -s name="$action_name" \
        -s enabled="$enabled" \
        -s defaultAction="$default_action"
}
