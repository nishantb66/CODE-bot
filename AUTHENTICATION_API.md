# 🔐 Authentication API Documentation

## Overview

This is a comprehensive, production-ready Django authentication system with the following features:

- ✅ **JWT Token Authentication** (Access + Refresh tokens)
- ✅ **Secure httpOnly Cookies** (tokens not accessible from JavaScript)
- ✅ **User Registration** (username, email, password)
- ✅ **User Login** (username/email + password)
- ✅ **Google OAuth SSO** (Sign in with Google)
- ✅ **Token Refresh** (30-minute access tokens, 7-day refresh tokens)
- ✅ **Password Management** (change password)
- ✅ **Token Revocation** (logout, logout from all devices)
- ✅ **Unique Email & Username** validation
- ✅ **Production-ready** with clean, maintainable code

---

## 🏗️ Architecture

### Security Features

1. **httpOnly Cookies**: Tokens are stored in httpOnly cookies, preventing XSS attacks
2. **CSRF Protection**: SameSite cookie attribute and Django CSRF middleware
3. **Token Revocation**: Refresh tokens can be revoked (database-backed)
4. **Short-lived Access Tokens**: 30-minute expiry reduces risk of token theft
5. **Long-lived Refresh Tokens**: 7-day expiry with revocation support
6. **Password Hashing**: Django's built-in PBKDF2 algorithm
7. **CORS Configuration**: Controlled cross-origin requests

### Token Flow

```
1. User logs in → Server generates access + refresh tokens
2. Tokens stored in httpOnly cookies (secure)
3. Frontend makes requests → Access token sent automatically
4. Access token expires (30 min) → Frontend calls /refresh/
5. New access token generated from refresh token
6. Refresh token expires (7 days) → User must login again
```

---

## 📋 API Endpoints

Base URL: `http://localhost:8000/api/auth/`

### 1. **Register User**

**Endpoint:** `POST /api/auth/register/`

**Description:** Create a new user account

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePassword123!",
  "password_confirm": "SecurePassword123!",
  "first_name": "John",  // optional
  "last_name": "Doe"      // optional
}
```

**Response (201 Created):**
```json
{
  "message": "Registration successful",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "is_email_verified": false,
    "profile_picture": null,
    "google_id": null,
    "date_joined": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Cookies Set:**
- `access_token` (httpOnly, 30 min)
- `refresh_token` (httpOnly, 7 days)

**Validation:**
- Username: minimum 3 characters, alphanumeric + underscore/hyphen
- Email: valid format, unique
- Password: Django default validators (min 8 chars, not too common, etc.)
- Username & Email: case-insensitive uniqueness

---

### 2. **Login**

**Endpoint:** `POST /api/auth/login/`

**Description:** Authenticate user with username/email and password

**Request Body:**
```json
{
  "username": "johndoe",  // OR email: "john@example.com"
  "password": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "is_email_verified": false,
    "profile_picture": null,
    "google_id": null,
    "date_joined": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Cookies Set:**
- `access_token` (httpOnly, 30 min)
- `refresh_token` (httpOnly, 7 days)

**Notes:**
- Can login with either username OR email
- Case-insensitive email matching

---

### 3. **Logout**

**Endpoint:** `POST /api/auth/logout/`

**Description:** Logout user and revoke refresh token

**Authentication:** Required (access token in cookie)

**Request Body:** None

**Response (200 OK):**
```json
{
  "message": "Logout successful"
}
```

**Cookies Cleared:**
- `access_token`
- `refresh_token`

---

### 4. **Refresh Access Token**

**Endpoint:** `POST /api/auth/refresh/`

**Description:** Get a new access token using refresh token

**Authentication:** None (refresh token from cookie)

**Request Body:** None

**Response (200 OK):**
```json
{
  "message": "Token refreshed successfully"
}
```

**Cookies Updated:**
- `access_token` (new token, 30 min)

**Error (401 Unauthorized):**
```json
{
  "error": "Refresh token has expired"
}
```

---

### 5. **Google OAuth - Get Login URL**

**Endpoint:** `GET /api/auth/google/login/`

**Description:** Get Google OAuth authorization URL

**Request:** None

**Response (200 OK):**
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/auth?..."
}
```

**Usage:**
1. Frontend calls this endpoint
2. Redirect user to `authorization_url`
3. User authorizes in Google
4. Google redirects to `redirect_uri` with `code` parameter
5. Frontend sends `code` to `/api/auth/google/` endpoint

---

### 6. **Google OAuth - Authenticate**

**Endpoint:** `POST /api/auth/google/`

**Description:** Authenticate user with Google OAuth code

**Request Body:**
```json
{
  "code": "4/0AY0e-g...",  // Authorization code from Google
  "redirect_uri": "http://localhost:8000/sso/google/callback/"  // optional
}
```

**Response (200 OK):**
```json
{
  "message": "Google authentication successful",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "is_email_verified": true,
    "profile_picture": "https://...",
    "google_id": "1234567890",
    "date_joined": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Cookies Set:**
- `access_token` (httpOnly, 30 min)
- `refresh_token` (httpOnly, 7 days)

**Behavior:**
- If user with Google ID exists → login
- If user with email exists → link Google account and login
- Otherwise → create new user and login

---

### 7. **Get Current User**

**Endpoint:** `GET /api/auth/me/`

**Description:** Get current authenticated user's information

**Authentication:** Required (access token in cookie)

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "is_email_verified": true,
  "profile_picture": "https://...",
  "google_id": null,
  "date_joined": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

---

### 8. **Change Password**

**Endpoint:** `POST /api/auth/change-password/`

**Description:** Change user's password

**Authentication:** Required (access token in cookie)

**Request Body:**
```json
{
  "old_password": "OldPassword123!",
  "new_password": "NewPassword123!",
  "new_password_confirm": "NewPassword123!"
}
```

**Response (200 OK):**
```json
{
  "message": "Password changed successfully"
}
```

**Cookies Updated:**
- `access_token` (new token, 30 min)
- `refresh_token` (new token, 7 days)

**Notes:**
- All existing refresh tokens are revoked for security
- New tokens are generated

---

### 9. **Revoke All Tokens (Logout from All Devices)**

**Endpoint:** `POST /api/auth/revoke-all/`

**Description:** Revoke all refresh tokens for the current user

**Authentication:** Required (access token in cookie)

**Response (200 OK):**
```json
{
  "message": "Successfully revoked 3 tokens",
  "tokens_revoked": 3
}
```

**Cookies Cleared:**
- `access_token`
- `refresh_token`

---

## 🔧 Configuration

### Environment Variables

Add these to your `.env` file:

```env
# Google OAuth Credentials
GOOGLE_OAUTH_CLIENT_ID=43901511010-fdjrk6v61itcat1o95j689bug4kflri3.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=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
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/sso/google/callback/

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

### Token Settings

```python
ACCESS_TOKEN_LIFETIME = 30 minutes
REFRESH_TOKEN_LIFETIME = 7 days
```

To modify, update `analyzer/settings.py`:

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    # ... other settings
}
```

---

## 🚀 Setup & Testing

### 1. Run Migrations

```bash
source venv/bin/activate
python manage.py makemigrations
python manage.py migrate
```

### 2. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 3. Run Server

```bash
python manage.py runserver
```

### 4. Test Endpoints

**Register:**
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPassword123!",
    "password_confirm": "TestPassword123!"
  }' \
  -c cookies.txt -b cookies.txt
```

**Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "TestPassword123!"
  }' \
  -c cookies.txt -b cookies.txt
```

**Get Current User:**
```bash
curl -X GET http://localhost:8000/api/auth/me/ \
  -b cookies.txt
```

**Logout:**
```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -b cookies.txt
```

---

## 📁 Project Structure

```
authentication/
├── models.py                    # User and RefreshToken models
├── serializers.py               # API serializers
├── views.py                     # API views
├── urls.py                      # URL routing
├── admin.py                     # Django admin configuration
├── middleware.py                # JWT cookie authentication middleware
├── services/
│   ├── __init__.py
│   ├── jwt_service.py          # JWT token management
│   └── google_oauth_service.py # Google OAuth integration
└── management/
    └── commands/
        └── cleanup_expired_tokens.py  # Token cleanup command
```

---

## 🛡️ Security Best Practices

### Current Implementation

✅ **httpOnly Cookies**: Tokens not accessible from JavaScript
✅ **Secure Cookies**: HTTPS in production
✅ **SameSite Cookies**: CSRF protection
✅ **Short-lived Access Tokens**: 30 minutes
✅ **Token Revocation**: Database-backed refresh tokens
✅ **Password Hashing**: Django's PBKDF2 algorithm
✅ **CORS Configuration**: Controlled origins
✅ **Input Validation**: Comprehensive serializers
✅ **SQL Injection Protection**: Django ORM
✅ **XSS Protection**: Django templates auto-escape

### Additional Recommendations

- [ ] Enable HTTPS in production
- [ ] Add rate limiting (django-ratelimit)
- [ ] Implement email verification
- [ ] Add 2FA support
- [ ] Monitor failed login attempts
- [ ] Set up logging and alerts
- [ ] Regular security audits

---

## 🧹 Maintenance

### Cleanup Expired Tokens

Run periodically (e.g., daily cron job):

```bash
python manage.py cleanup_expired_tokens
```

### Monitor Token Usage

```python
# In Django shell
from authentication.models import RefreshToken

# Total tokens
RefreshToken.objects.count()

# Active tokens
RefreshToken.objects.filter(is_revoked=False).count()

# Expired tokens
from django.utils import timezone
RefreshToken.objects.filter(expires_at__lt=timezone.now()).count()
```

---

## 🐛 Troubleshooting

### Issue: Tokens not being sent in requests

**Solution:** Ensure cookies are enabled and CORS is configured correctly:
```python
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = ['http://localhost:3000']
```

### Issue: Google OAuth fails

**Solution:** 
1. Check credentials in `.env`
2. Verify redirect URI matches Google Console
3. Ensure redirect URI is whitelisted in Google Console

### Issue: Token expired immediately

**Solution:** Check server time is synchronized (NTP)

---

## 📊 Database Schema

### User Model

```sql
Table: users
- id: BigInt (PK)
- username: VARCHAR(150) UNIQUE
- email: VARCHAR(254) UNIQUE
- password: VARCHAR(128)
- first_name: VARCHAR(150)
- last_name: VARCHAR(150)
- google_id: VARCHAR(255) UNIQUE NULL
- is_email_verified: BOOLEAN
- profile_picture: VARCHAR(200) NULL
- is_active: BOOLEAN
- is_staff: BOOLEAN
- is_superuser: BOOLEAN
- date_joined: TIMESTAMP
- updated_at: TIMESTAMP
- last_login: TIMESTAMP NULL
```

### RefreshToken Model

```sql
Table: refresh_tokens
- id: BigInt (PK)
- user_id: BigInt (FK -> users.id)
- token: VARCHAR(500) UNIQUE
- jti: VARCHAR(255) UNIQUE
- created_at: TIMESTAMP
- expires_at: TIMESTAMP
- ip_address: VARCHAR(45) NULL
- user_agent: TEXT
- is_revoked: BOOLEAN
- revoked_at: TIMESTAMP NULL
```

---

## 🎯 Next Steps

Now that the backend is complete, you can proceed with frontend implementation!

Ready when you are! 🚀
