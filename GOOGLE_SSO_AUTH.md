# 🔐 Authentication System Refactor - Google SSO Only

## Overview

The authentication system has been completely refactored to use **Google SSO as the only authentication method**. All username/password-based authentication has been removed.

## Key Changes

### 1. Authentication Method
- ✅ **Google SSO Only** - All authentication happens through Google
- ❌ Removed username/password login
- ❌ Removed user registration form
- ❌ Removed password change functionality

### 2. Database
- ✅ **MongoDB Only** - All user data stored in MongoDB
- Collection name: `users`
- Token storage: `refresh_tokens` collection
- No more SQLite for auth (Django admin still uses SQLite)

### 3. User Flow

#### Existing User (email in database)
1. User clicks "Continue with Google"
2. Google OAuth flow completes
3. System verifies user exists in MongoDB
4. User is logged in immediately
5. Redirected to authenticated area

#### New User (email not in database)
1. User clicks "Continue with Google"
2. Google OAuth flow completes
3. System detects new email
4. **Confirmation prompt shown**:
   - "Do you want to continue and create an account using this Google email?"
   - Displays email and name from Google
5. If YES → User created in MongoDB → Logged in → Redirected
6. If NO → No record created → Returned to login page

## API Endpoints

### Authentication APIs

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/auth/api/google/login/` | GET | Get Google OAuth URL | No |
| `/api/auth/api/google/` | POST | Process OAuth code (login or prompt for signup) | No |
| `/api/auth/api/google/signup/` | POST | Create new user (after confirmation) | No |
| `/api/auth/api/logout/` | POST | Logout user | Yes |
| `/api/auth/api/refresh/` | POST | Refresh access token | No |
| `/api/auth/api/me/` | GET | Get current user info | Yes |
| `/api/auth/api/revoke-all/` | POST | Revoke all tokens | Yes |

### Web Pages

| Path | Description |
|------|-------------|
| `/auth/login/` | Login page with Google SSO button |
| `/sso/google/callback/` | Google OAuth callback handler |

## Protected Routes

**All routes are protected** except:
- `/auth/login/` - Login page
- `/auth/google/callback/` - OAuth callback
- `/sso/google/callback/` - OAuth callback
- `/api/auth/api/google/*` - Auth API endpoints
- `/admin/` - Django admin (has its own auth)
- Static and media files

### Behavior for Unauthenticated Users:
- **Web requests**: Redirected to `/auth/login/`
- **API requests**: Returns `401 Unauthorized` with JSON:
  ```json
  {"error": "Authentication required", "code": "UNAUTHORIZED"}
  ```

## MongoDB Collections

### `users` Collection Schema
```javascript
{
  _id: ObjectId,
  email: String (unique, lowercase),
  name: String,
  first_name: String,
  last_name: String,
  google_id: String (unique),
  profile_picture: String (URL),
  auth_provider: "google",
  is_active: Boolean,
  is_email_verified: Boolean,
  created_at: DateTime,
  updated_at: DateTime,
  last_login: DateTime
}
```

### `refresh_tokens` Collection Schema
```javascript
{
  _id: ObjectId,
  user_email: String,
  token: String,
  jti: String (unique, JWT ID),
  created_at: DateTime,
  expires_at: DateTime,
  ip_address: String,
  user_agent: String,
  is_revoked: Boolean,
  revoked_at: DateTime
}
```

## JWT Token Handling

- **Access Token**: 30 minutes lifetime, stored in httpOnly cookie
- **Refresh Token**: 7 days lifetime, stored in httpOnly cookie
- Tokens are signed with Django's SECRET_KEY using HS256 algorithm
- Refresh tokens are stored in MongoDB for revocation support

## Files Modified/Created

### New Files
- `authentication/services/mongodb_user_service.py` - MongoDB user operations
- `authentication/services/mongodb_token_service.py` - MongoDB token operations

### Modified Files
- `authentication/views.py` - Google SSO only views
- `authentication/urls.py` - Updated URL patterns
- `authentication/middleware.py` - MongoDB-based auth middleware
- `authentication/login_required_middleware.py` - Updated exempt paths
- `authentication/authentication.py` - DRF authentication with MongoDB
- `authentication/serializers.py` - Google SSO serializers only
- `authentication/web_views.py` - Removed SignupView
- `authentication/services/google_oauth_service.py` - Updated for MongoDB
- `authentication/services/jwt_service.py` - Pure PyJWT with MongoDB
- `authentication/services/__init__.py` - Updated exports
- `authentication/templates/authentication/login.html` - Google SSO only UI
- `authentication/templates/authentication/google_callback.html` - New user confirmation flow
- `requirements.txt` - Added PyJWT

### Removed Files
- `authentication/templates/authentication/signup.html` - No longer needed

## Security Features

1. **httpOnly Cookies** - Tokens cannot be accessed by JavaScript
2. **Secure Cookies** - HTTPS only in production
3. **SameSite=Lax** - CSRF protection
4. **Token Revocation** - Stored in MongoDB, can be revoked anytime
5. **User Confirmation** - Explicit consent before account creation
6. **No Password Storage** - All auth through Google

## Testing

### Verify Login Page
```bash
curl http://127.0.0.1:8000/auth/login/
```

### Verify Route Protection
```bash
# Should redirect to login
curl -I http://127.0.0.1:8000/

# Should return 401
curl http://127.0.0.1:8000/api/auth/api/me/
```

### Verify Google OAuth URL
```bash
curl http://127.0.0.1:8000/api/auth/api/google/login/
```

## Environment Variables Required

```env
# Google OAuth
GOOGLE_OAUTH_CLIENT_ID=your_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/sso/google/callback/

# MongoDB
MONGODB_URI=your_mongodb_connection_string
MONGODB_DB_NAME=github_bot_db
```

## Migration Notes

1. Users created before this refactor (with username/password) will need to:
   - Sign in with Google using the same email
   - The system will find their existing user record by email

2. The Django `users` table in SQLite is still used by Django admin.
   - MongoDB `users` collection is the source of truth for app authentication

3. To fully migrate to MongoDB-only, you would need to:
   - Create a custom Django admin that uses MongoDB
   - Or disable Django admin for user management
