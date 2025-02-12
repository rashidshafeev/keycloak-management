# Token Management with Keycloak

## Frontend Token Management

```typescript
// frontend/src/auth/tokenManager.ts
class TokenManager {
  private accessToken: string | null = null;
  private tokenExpiryTime: number = 0;

  setTokens(accessToken: string, expiresIn: number) {
    this.accessToken = accessToken;
    this.tokenExpiryTime = Date.now() + expiresIn * 1000;
  }

  getAccessToken(): string | null {
    if (this.isTokenExpired()) {
      this.refreshToken();
    }
    return this.accessToken;
  }

  private isTokenExpired(): boolean {
    return Date.now() >= this.tokenExpiryTime - 30000; // 30 seconds buffer
  }

  private async refreshToken() {
    try {
      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        credentials: 'include', // Important for cookies
      });
      const { access_token, expires_in } = await response.json();
      this.setTokens(access_token, expires_in);
    } catch (error) {
      // Handle refresh failure (redirect to login)
      window.location.href = '/login';
    }
  }
}

// Usage in API calls
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(config => {
  const token = tokenManager.getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

## Backend Token Validation (NestJS Example)

```typescript
// backend/src/auth/auth.module.ts
import { Module } from '@nestjs/common';
import { AuthGuard, KeycloakConnectModule } from 'nest-keycloak-connect';

@Module({
  imports: [
    KeycloakConnectModule.register({
      authServerUrl: 'https://auth.fawz.app',
      realm: 'fawz',
      clientId: 'fawz-api',
      secret: process.env.KEYCLOAK_SECRET,
    }),
  ],
  providers: [
    // Global guard, authenticate all endpoints
    {
      provide: APP_GUARD,
      useClass: AuthGuard,
    },
  ],
})
export class AuthModule {}

// backend/src/posts/posts.controller.ts
import { Controller, Get, UseGuards } from '@nestjs/common';
import { AuthGuard, RoleGuard, Roles } from 'nest-keycloak-connect';

@Controller('posts')
@UseGuards(AuthGuard, RoleGuard)
export class PostsController {
  @Get()
  @Roles({ roles: ['user'] })
  findAll() {
    // Keycloak has already validated the token
    // User is authenticated and authorized
    return this.postsService.findAll();
  }
}
```

## Backend Token Validation (Express Example)

```typescript
// backend/src/middleware/auth.ts
import { auth } from 'express-oauth2-jwt-bearer';
import KeycloakConnect from 'keycloak-connect';
import session from 'express-session';

const memoryStore = new session.MemoryStore();
const keycloak = new KeycloakConnect({ store: memoryStore }, {
  realm: 'fawz',
  'auth-server-url': 'https://auth.fawz.app',
  'ssl-required': 'external',
  resource: 'fawz-api',
  'confidential-port': 0,
  'bearer-only': true,
});

app.use(session({
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: true,
  store: memoryStore,
}));

app.use(keycloak.middleware());

// Protected route
app.get('/api/protected', 
  keycloak.protect(), // Validates token
  (req, res) => {
    // Token is valid, user is authenticated
    res.json({ message: 'Protected data' });
  }
);

// Role-based protection
app.get('/api/admin', 
  keycloak.protect('realm:admin'), // Checks for admin role
  (req, res) => {
    res.json({ message: 'Admin data' });
  }
);
```

## Security Best Practices

### Frontend
1. **Token Storage**:
   ```typescript
   // BAD - Don't store in localStorage
   localStorage.setItem('token', accessToken);
   
   // GOOD - Store in memory
   private accessToken: string | null = null;
   ```

2. **Refresh Token**:
   ```typescript
   // Set refresh token in httpOnly cookie
   res.cookie('refreshToken', token, {
     httpOnly: true,
     secure: true,
     sameSite: 'strict',
     maxAge: 7 * 24 * 60 * 60 * 1000 // 7 days
   });
   ```

3. **Token Refresh Strategy**:
   ```typescript
   // Proactive refresh
   const REFRESH_THRESHOLD = 30000; // 30 seconds
   
   if (tokenExpiryTime - Date.now() < REFRESH_THRESHOLD) {
     await refreshToken();
   }
   ```

### Backend
1. **Token Validation**:
   ```typescript
   // Let Keycloak handle validation
   app.use(keycloak.middleware());
   app.use(keycloak.protect());
   ```

2. **Role Checking**:
   ```typescript
   // Check multiple roles
   @Roles({ roles: ['user', 'admin'] })
   async getProtectedData() {
     // User has required roles
   }
   ```

3. **Resource-Based Access**:
   ```typescript
   // Check resource permissions
   @Resource('posts')
   @Scopes(['read', 'write'])
   async managePosts() {
     // User has required permissions
   }
   ```
