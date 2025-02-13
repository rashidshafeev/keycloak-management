# Keycloak Implementation Guide

## 1. Authentication Flow

### 1.1 Identity Provider Configuration
Add to `identity-providers.yml`:
```yaml
identity_providers:
  - alias: "phone-auth"
    providerId: "custom"
    enabled: true
    updateProfileFirstLoginMode: "off"
    trustEmail: false
    storeToken: false
    addReadTokenRoleOnCreate: false
    config:
      authorizationUrl: "http://auth-service:3000/auth/phone"
      tokenUrl: "http://auth-service:3000/auth/token"
      clientId: "${PHONE_AUTH_CLIENT_ID}"
      clientSecret: "${PHONE_AUTH_CLIENT_SECRET}"
      defaultScope: "phone"
      backchannelSupported: "true"
```

### 1.2 Authentication Flow Configuration
Add to `authentication.yml`:
```yaml
browser_flow:
  alias: "browser"
  description: "Browser based authentication"
  providerId: "basic-flow"
  topLevel: true
  builtIn: false
  authenticationExecutions:
    - authenticator: "auth-cookie"
      requirement: "ALTERNATIVE"
      priority: 10
      
    - authenticator: "identity-provider-redirector"
      requirement: "ALTERNATIVE"
      priority: 20
      config:
        defaultProvider: "phone-auth"
      
    - flowAlias: "forms"
      requirement: "ALTERNATIVE"
      priority: 30
```

## 2. Event System

### 2.1 Event Configuration
Update in `events.yml`:
```yaml
listeners:
  - name: "http-webhook"
    enabled: true
    properties:
      url: "http://auth-service:3000/events"
      secret: "${EVENT_WEBHOOK_SECRET}"
      retries: 3
      timeout: 5000
      
included_events:
  # Authentication Events
  - LOGIN
  - LOGIN_ERROR
  - LOGOUT
  - CODE_TO_TOKEN
  - REFRESH_TOKEN
  
  # Identity Provider Events
  - IDENTITY_PROVIDER_LOGIN
  - IDENTITY_PROVIDER_LINK_ACCOUNT
  - IDENTITY_PROVIDER_RESPONSE
  
  # User Events
  - UPDATE_PROFILE
  - UPDATE_EMAIL
  - VERIFY_EMAIL
```

## 3. Metrics and Monitoring

### 3.1 Metrics Configuration
Add to `monitoring.yml`:
```yaml
metrics:
  enabled: true
  prefix: "keycloak"
  
  # Authentication Metrics
  authentication:
    enabled: true
    counters:
      - name: "auth_attempts_total"
        help: "Total number of authentication attempts"
        labels: ["provider", "outcome"]
      - name: "token_requests_total"
        help: "Total number of token requests"
        labels: ["provider", "grant_type"]
    histograms:
      - name: "auth_duration_seconds"
        help: "Duration of authentication process"
        buckets: [0.1, 0.5, 1, 2, 5]
        labels: ["provider"]
    gauges:
      - name: "active_sessions"
        help: "Number of active sessions"
        labels: ["provider"]

  # Identity Provider Metrics
  identity_provider:
    enabled: true
    counters:
      - name: "idp_requests_total"
        help: "Total number of identity provider requests"
        labels: ["provider", "type"]
      - name: "idp_responses_total"
        help: "Total number of identity provider responses"
        labels: ["provider", "outcome"]
```

### 3.2 Health Checks
Update in `monitoring.yml`:
```yaml
health:
  enabled: true
  checks:
    - name: "identity-providers"
      enabled: true
    - name: "token-service"
      enabled: true
    - name: "event-listener"
      enabled: true
```

## 4. Required Changes

### 4.1 Auth Service Implementation
1. Create endpoints in auth service:
   ```typescript
   // apps/auth-service/src/auth/controllers/phone.controller.ts
   @Controller('auth/phone')
   export class PhoneAuthController {
     @Post('authorize')
     async authorize(@Body() data: PhoneAuthDto) {
       // Handle phone number validation and OTP sending
     }
     
     @Post('verify')
     async verify(@Body() data: OtpVerifyDto) {
       // Verify OTP and return Keycloak tokens
     }
   }
   ```

2. Add token endpoint:
   ```typescript
   // apps/auth-service/src/auth/controllers/token.controller.ts
   @Controller('auth/token')
   export class TokenController {
     @Post()
     async getToken(@Body() data: TokenRequestDto) {
       // Exchange authorization code for tokens
     }
   }
   ```

3. Add event handler:
   ```typescript
   // apps/auth-service/src/auth/controllers/events.controller.ts
   @Controller('events')
   export class EventsController {
     @Post()
     async handleEvent(@Body() event: KeycloakEvent) {
       // Process Keycloak events
     }
   }
   ```

### 4.2 Environment Variables
Add to `.env`:
```env
# Phone Authentication
PHONE_AUTH_CLIENT_ID=phone-auth-client
PHONE_AUTH_CLIENT_SECRET=your-client-secret
PHONE_AUTH_REDIRECT_URI=http://localhost:8080/auth/realms/master/broker/phone-auth/endpoint

# SMS Provider
SMS_PROVIDER_URL=https://api.twilio.com/v1
SMS_PROVIDER_SID=${TWILIO_ACCOUNT_SID}
SMS_PROVIDER_TOKEN=${TWILIO_AUTH_TOKEN}
SMS_PROVIDER_FROM=${TWILIO_PHONE_NUMBER}

# Event System
EVENT_WEBHOOK_SECRET=your-webhook-secret
EVENT_BUS_RETRIES=3
EVENT_BUS_TIMEOUT=5000
```

### 4.3 Implementation Steps
1. Configure Identity Provider:
   ```bash
   # Update Keycloak config
   ./kcadm.sh create identity-provider/instances -r master -f identity-provider-config.json
   ```

2. Update Authentication Flow:
   ```bash
   # Set phone-auth as alternative authentication
   ./kcadm.sh update authentication/flows/browser -r master -f browser-flow.json
   ```

3. Configure Event Listener:
   ```bash
   # Enable webhook event listener
   ./kcadm.sh update events/config -r master -f event-config.json
   ```

4. Deploy Auth Service:
   ```bash
   # Deploy updated auth service
   kubectl apply -f k8s/auth-service.yaml
   ```
