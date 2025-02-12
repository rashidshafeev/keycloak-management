# Fawz SSO Developer Guide

## Getting Started with Fawz SSO

### 1. Register Your Application

1. Visit the developer portal: https://developers.fawz.app
2. Create a new application:
   - Name: Your application name
   - Redirect URIs: Your application callback URLs
   - Application type: public (SPA) or confidential (server)

### 2. Client Configuration

You'll receive:
- Client ID
- Client Secret (for confidential clients)
- Configuration URLs

### 3. Required Settings

```javascript
const config = {
  realm: 'fawz',
  authServerUrl: 'https://auth.fawz.app',
  resource: 'your-client-id',
  // For confidential clients
  credentials: {
    secret: 'your-client-secret'
  },
  // Required settings
  pkce: true,
  redirectUri: 'https://your-app.com/callback',
  // Recommended scopes
  scope: 'openid profile email'
};
```

### 4. Available Scopes

- `fawz-basic`: Basic user info (always granted)
- `fawz-profile`: Extended profile info
- `fawz-bulletin`: Bulletin board specific permissions

### 5. User Roles

- `fawz_user`: Basic user access
- `fawz_verified`: Verified user access
- Custom roles available upon request

## Security Requirements

1. **PKCE Flow**
   - Required for all public clients
   - Recommended for confidential clients

2. **Token Handling**
   - Never store tokens in localStorage
   - Use secure httpOnly cookies
   - Implement proper token refresh

3. **SSL/TLS**
   - HTTPS required in production
   - Valid SSL certificate

## Integration Examples

### Web Application (React)
```typescript
import { KeycloakProvider } from '@react-keycloak/web';

const keycloakConfig = {
  url: 'https://auth.fawz.app',
  realm: 'fawz',
  clientId: 'your-client-id'
};

function App() {
  return (
    <KeycloakProvider keycloak={keycloak}>
      <YourApp />
    </KeycloakProvider>
  );
}
```

### Backend (Node.js)
```typescript
import { auth } from 'express-oauth2-jwt-bearer';

const checkJwt = auth({
  audience: 'your-api-identifier',
  issuerBaseURL: 'https://auth.fawz.app/realms/fawz'
});

app.get('/api/protected', checkJwt, (req, res) => {
  res.json({ message: 'Protected endpoint' });
});
```

## Best Practices

1. **Error Handling**
   - Implement proper error pages
   - Handle token expiration
   - Graceful degradation

2. **User Experience**
   - Clear login/logout flows
   - Proper loading states
   - Error messages

3. **Security**
   - Regular security updates
   - Token validation
   - XSS protection

## Testing

1. **Test Environment**
   ```
   Auth Server: https://auth-test.fawz.app
   Realm: fawz-test
   ```

2. **Test Accounts**
   - Available upon request
   - Different role combinations

3. **Test Flows**
   - Login/Logout
   - Token refresh
   - Error scenarios

## Support

- Developer Portal: https://developers.fawz.app
- Documentation: https://docs.fawz.app
- Support Email: developers@fawz.app

## Rate Limits

- Development: 100 requests/hour
- Production: Based on agreement
- Burst: 50 requests/minute

## Monitoring

- Status page: https://status.fawz.app
- API metrics available in developer portal
- Real-time usage statistics
