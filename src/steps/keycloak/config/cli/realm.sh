#!/bin/bash

# Get Keycloak container ID
KEYCLOAK_CONTAINER=$(docker ps --filter "name=keycloak" --format "{{.ID}}")

if [ -z "$KEYCLOAK_CONTAINER" ]; then
    echo "Error: Keycloak container not found"
    exit 1
fi

echo "Using Keycloak container: $KEYCLOAK_CONTAINER"

# Wait for Keycloak to be ready
echo "Waiting for Keycloak to be ready..."
max_attempts=30
attempt=1
while [ $attempt -le $max_attempts ]; do
    if docker exec $KEYCLOAK_CONTAINER curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health | grep -q "200"; then
        echo "Keycloak is ready!"
        break
    fi
    echo "Attempt $attempt/$max_attempts - Keycloak not ready yet..."
    sleep 5
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    echo "Error: Keycloak did not become ready in time"
    exit 1
fi

# Execute commands inside the container
echo "Configuring Keycloak admin credentials..."
docker exec $KEYCLOAK_CONTAINER /opt/keycloak/bin/kcadm.sh config credentials \
    --server http://localhost:8080 \
    --realm master \
    --user admin \
    --password admin \
    --client admin-cli

if [ $? -ne 0 ]; then
    echo "Error: Failed to configure admin credentials"
    exit 1
fi

echo "Creating realm configuration..."
docker exec $KEYCLOAK_CONTAINER /opt/keycloak/bin/kcadm.sh create realms \
    -s realm="my-realm" \
    -s enabled=true \
    -s displayName="My Realm" \
    -s sslRequired=EXTERNAL \
    -s registrationAllowed=false \
    -s loginWithEmailAllowed=true \
    -s duplicateEmailsAllowed=false \
    -s resetPasswordAllowed=true \
    -s editUsernameAllowed=false \
    -s bruteForceProtected=true \
    -o || true

if [ $? -ne 0 ]; then
    echo "Note: Realm might already exist, continuing..."
fi

echo "Updating realm settings..."
docker exec $KEYCLOAK_CONTAINER /opt/keycloak/bin/kcadm.sh update realms/my-realm \
    -s "defaultSignatureAlgorithm=RS256" \
    -s "revokeRefreshToken=true" \
    -s "refreshTokenMaxReuse=0" \
    -s "ssoSessionIdleTimeout=1800" \
    -s "ssoSessionMaxLifespan=36000" \
    -s "accessTokenLifespan=300" \
    -s "accessTokenLifespanForImplicitFlow=900" \
    -s "offlineSessionIdleTimeout=2592000"

if [ $? -ne 0 ]; then
    echo "Error: Failed to update realm settings"
    exit 1
fi

echo "Verifying realm configuration..."
REALM_INFO=$(docker exec $KEYCLOAK_CONTAINER /opt/keycloak/bin/kcadm.sh get realms/my-realm)

if [ $? -eq 0 ]; then
    echo "Realm configuration verified:"
    echo "$REALM_INFO"
    echo "Realm configuration completed successfully!"
else
    echo "Error: Failed to verify realm configuration"
    exit 1
fi
