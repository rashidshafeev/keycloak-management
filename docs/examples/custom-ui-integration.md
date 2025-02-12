# Custom UI Integration with Keycloak SSO

## OAuth2/OIDC Endpoints

Your Keycloak instance exposes these standard endpoints:

```
Authorization: https://auth.fawz.app/realms/fawz/protocol/openid-connect/auth
Token: https://auth.fawz.app/realms/fawz/protocol/openid-connect/token
UserInfo: https://auth.fawz.app/realms/fawz/protocol/openid-connect/userinfo
Logout: https://auth.fawz.app/realms/fawz/protocol/openid-connect/logout
```

## Example Integration (React)

```typescript
// auth.config.ts
export const authConfig = {
  authority: 'https://auth.fawz.app/realms/fawz',
  clientId: 'your-client-id',
  redirectUri: 'https://your-app.com/callback',
  responseType: 'code',
  scope: 'openid profile email',
  pkce: true // Always use PKCE
};

// CustomLoginButton.tsx
const CustomLoginButton = () => {
  const login = async () => {
    const params = new URLSearchParams({
      client_id: authConfig.clientId,
      redirect_uri: authConfig.redirectUri,
      response_type: 'code',
      scope: authConfig.scope,
      // Add PKCE challenge here
    });

    window.location.href = `${authConfig.authority}/protocol/openid-connect/auth?${params}`;
  };

  return <button onClick={login}>Login with Fawz</button>;
};

// CustomLoginForm.tsx
const CustomLoginForm = () => {
  const handleSubmit = async (username: string, password: string) => {
    const response = await fetch(`${authConfig.authority}/protocol/openid-connect/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'password',
        client_id: authConfig.clientId,
        username,
        password,
      })
    });
    
    const tokens = await response.json();
    // Handle tokens (store securely)
  };

  return (
    <form onSubmit={...}>
      {/* Your custom UI */}
    </form>
  );
};
```

## Example Integration (Next.js)

```typescript
// app/api/auth/[...nextauth]/route.ts
import NextAuth from 'next-auth';
import KeycloakProvider from 'next-auth/providers/keycloak';

export const authOptions = {
  providers: [
    KeycloakProvider({
      clientId: process.env.KEYCLOAK_ID,
      clientSecret: process.env.KEYCLOAK_SECRET,
      issuer: process.env.KEYCLOAK_ISSUER,
    })
  ],
  // Custom pages
  pages: {
    signIn: '/auth/signin',
    signOut: '/auth/signout',
    error: '/auth/error',
  }
};

export const handler = NextAuth(authOptions);
```

## Security Best Practices

1. **Always Use PKCE**:
   - Prevents authorization code interception
   - Required for public clients

2. **Token Storage**:
   - Store access tokens in memory
   - Store refresh tokens in httpOnly cookies
   - Never store in localStorage

3. **Token Validation**:
   - Validate token signatures
   - Check expiration times
   - Verify audience and issuer

4. **Error Handling**:
   - Handle token expiration gracefully
   - Implement refresh token rotation
   - Clear tokens on logout

## API Integration

```typescript
// api.ts
const api = axios.create({
  baseURL: 'https://api.your-app.com'
});

api.interceptors.request.use(config => {
  const token = getAccessToken(); // Your token management
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      // Handle token refresh
      const newToken = await refreshAccessToken();
      error.config.headers.Authorization = `Bearer ${newToken}`;
      return api(error.config);
    }
    return Promise.reject(error);
  }
);
```

## Registration Flow Example

```typescript
const register = async (userData: UserData) => {
  const response = await fetch(`${authConfig.authority}/protocol/openid-connect/registrations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: userData.username,
      email: userData.email,
      firstName: userData.firstName,
      lastName: userData.lastName,
      credentials: [{
        type: 'password',
        value: userData.password,
        temporary: false
      }]
    })
  });

  if (response.ok) {
    // Proceed with login
    return login(userData.username, userData.password);
  }
};
```
