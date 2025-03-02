#!/bin/bash

# Configure events for a realm
configure_realm_events() {
    local realm=$1
    local admin_user=$2
    local admin_password=$3
    local event_config=$4

    # Authenticate
    ./kcadm.sh config credentials \
        --server http://localhost:8080 \
        --realm master \
        --user "$admin_user" \
        --password "$admin_password"

    # Enable events
    ./kcadm.sh update events/config \
        -r "$realm" \
        -s "eventsEnabled=true" \
        -s "eventsExpiration=2592000" \
        -s "adminEventsEnabled=true" \
        -s "adminEventsDetailsEnabled=false"

    # Configure event types
    ./kcadm.sh update events/config \
        -r "$realm" \
        -s 'enabledEventTypes=["LOGIN","LOGIN_ERROR","REGISTER","REGISTER_ERROR","LOGOUT","UPDATE_PROFILE","UPDATE_PASSWORD","UPDATE_EMAIL","VERIFY_EMAIL","REMOVE_ACCOUNT"]'

    # Configure event listeners
    ./kcadm.sh update events/config \
        -r "$realm" \
        -s 'eventsListeners=["jboss-logging","http-webhook"]'

    # Configure webhook listener
    ./kcadm.sh create components \
        -r "$realm" \
        -s name=webhook-event-listener \
        -s providerId=http-webhook \
        -s providerType=org.keycloak.events.EventListenerProvider \
        -s 'config.{"webhook.url":["http://event-bus:3000/events"],"webhook.secret":["${EVENT_WEBHOOK_SECRET}"],"webhook.retries":["3"],"webhook.timeout":["5000"]}'
}
