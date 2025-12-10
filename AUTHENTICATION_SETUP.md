# 🔐 Authentication System Setup Guide

## ✨ Features Implemented

Your Django application now has a **production-ready, secure authentication system** with:

✅ **JWT Token Authentication** (Access: 30 min, Refresh: 7 days)  
✅ **Secure httpOnly Cookies** (tokens hidden from JavaScript/XSS attacks)  
✅ **User Registration** (username, email, password with validation)  
✅ **User Login** (supports both username and email)  
✅ **Google OAuth SSO** (Sign in with Google)  
✅ **Token Refresh** (automatic token renewal)  
✅ **Password Management** (secure password change)  
✅ **Token Revocation** (logout from single/all devices)  
✅ **Unique Email & Username** constraints  
✅ **Clean, Maintainable Code** (professional structure)

---

## 🚀 Quick Start

### 1. **Add Environment Variables**

Add these to your `.env` file:

```env
# Google OAuth Credentials
GOOGLE_OAUTH_CLIENT_ID=43901511010-fdjrk6v61itcat1o95j689bug4kflri3.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=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
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/sso/google/callback/

# CORS Configuration (for frontend)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

### 2. **Create Admin User (Optional)**

```bash
source venv/bin/activate
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### 3. **Start the Server**

The server should already be running. If not:

```bash
source venv/bin/activate
python manage.py runserver
```

### 4. **Test the API**

Run the automated test script:

```bash
source venv/bin/activate
python test_auth.py
```

Or test manually with curl:

```bash
# Register a user
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }' \
  -c cookies.txt

# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "SecurePass123!"
  }' \
  -c cookies.txt -b cookies.txt

# Get current user
curl http://localhost:8000/api/auth/me/ \
  -b cookies.txt

# Logout
curl -X POST http://localhost:8000/api/auth/logout/ \
  -b cookies.txt
```

---

## 📋 Available API Endpoints

All endpoints are prefixed with `/api/auth/`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/register/` | Register new user | No |
| POST | `/login/` | Login user | No |
| POST | `/logout/` | Logout user | Yes |
| POST | `/refresh/` | Refresh access token | No (cookie) |
| GET | `/google/login/` | Get Google OAuth URL | No |
| POST | `/google/` | Authenticate with Google | No |
| GET | `/me/` | Get current user | Yes |
| POST | `/change-password/` | Change password | Yes |
| POST | `/revoke-all/` | Logout from all devices | Yes |

📖 **Full API Documentation:** See [AUTHENTICATION_API.md](AUTHENTICATION_API.md)

---

## 🏗️ Project Structure

```
authentication/
├── models.py                          # User & RefreshToken models
├── serializers.py                     # API serializers & validation
├── views.py                           # API endpoints
├── urls.py                            # URL routing
├── admin.py                           # Django admin config
├── middleware.py                      # JWT cookie authentication
├── services/
│   ├── __init__.py
│   ├── jwt_service.py                 # JWT token management
│   └── google_oauth_service.py        # Google OAuth integration
├── management/
│   └── commands/
│       └── cleanup_expired_tokens.py  # Token cleanup utility
└── migrations/
    └── 0001_initial.py                # Database schema
```

---

## 🔒 Security Features

### ✅ What's Secure

1. **httpOnly Cookies**
   - Tokens stored in httpOnly cookies
   - Not accessible via JavaScript
   - Prevents XSS token theft

2. **CSRF Protection**
   - SameSite cookie attribute
   - Django CSRF middleware
   - Cross-site request forgery prevention

3. **Token Expiry**
   - Access tokens: 30 minutes
   - Refresh tokens: 7 days
   - Limits exposure window

4. **Token Revocation**
   - Database-backed refresh tokens
   - Can revoke individual or all tokens
   - Immediate logout capability

5. **Password Security**
   - Django's PBKDF2 hashing
   - Minimum 8 characters
   - Complexity validation
   - Common password checks

6. **Input Validation**
   - Comprehensive serializers
   - Email format validation
   - Username constraints
   - SQL injection protection (ORM)

7. **HTTPS Ready**
   - Secure cookies in production
   - HSTS headers
   - SSL redirect

---

## 🔧 Configuration

### Token Lifetimes

Modify in `analyzer/settings.py`:

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),   # Change here
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),      # Change here
    # ...
}
```

### CORS Settings

Update allowed origins in `.env`:

```env
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://yourfrontend.com
```

### Google OAuth

1. **Google Cloud Console Setup:**
   - Create project at https://console.cloud.google.com
   - Enable Google+ API
   - Create OAuth 2.0 credentials
   - Add authorized redirect URIs:
     - `http://localhost:8000/sso/google/callback/`
     - Your production callback URL

2. **Update Credentials:**
   - Replace values in `.env` file
   - Ensure redirect URI matches exactly

---

## 📊 Database Models

### User Model

- Custom Django user model
- Fields: username, email, password, first_name, last_name
- Google OAuth: google_id, is_email_verified, profile_picture
- Unique constraints on email and username

### RefreshToken Model

- Stores refresh tokens for revocation
- Tracks: user, token, JTI, expiry, IP, user agent
- Enables logout from all devices
- Automatic cleanup capability

---

## 🧹 Maintenance

### Clean Up Expired Tokens

Run periodically (e.g., daily cron job):

```bash
python manage.py cleanup_expired_tokens
```

### Monitor Token Usage

Django admin: http://localhost:8000/admin/

- View all users
- See active refresh tokens
- Revoke tokens manually
- Check token metadata

---

## 🧪 Testing

### Automated Tests

```bash
# Run the test script
python test_auth.py
```

### Manual Testing

```bash
# Test with cURL (see examples above)

# Test with Postman
# Import the following collection:
- Create requests for each endpoint
- Use cookie persistence
- Test error cases
```

### Test Scenarios

✅ User registration with validation  
✅ Login with username  
✅ Login with email  
✅ Invalid credentials  
✅ Token refresh  
✅ Expired token handling  
✅ Logout and cookie clearing  
✅ Password change  
✅ Google OAuth flow  
✅ Revoke all tokens  

---

## 🐛 Troubleshooting

### Issue: "CSRF token missing"

**Solution:** Ensure cookies are being sent with requests:
```javascript
// Frontend fetch example
fetch(url, {
  credentials: 'include',  // Important!
  ...
})
```

### Issue: "Access token expired"

**Solution:** Call `/api/auth/refresh/` to get new access token

### Issue: "Google OAuth fails"

**Solutions:**
1. Check credentials in `.env`
2. Verify redirect URI matches Google Console
3. Ensure redirect URI is whitelisted
4. Check that Google+ API is enabled

### Issue: Cookies not being set

**Solutions:**
1. Check CORS settings allow credentials
2. Ensure `SameSite` is compatible with your setup
3. In development, use `http://localhost` (not `127.0.0.1` if origin is `localhost`)

---

## 🌐 Frontend Integration

### JavaScript Fetch Example

```javascript
// Register
const register = async (userData) => {
  const response = await fetch('http://localhost:8000/api/auth/register/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',  // Important for cookies!
    body: JSON.stringify(userData)
  });
  return response.json();
};

// Login
const login = async (username, password) => {
  const response = await fetch('http://localhost:8000/api/auth/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ username, password })
  });
  return response.json();
};

// Get current user
const getCurrentUser = async () => {
  const response = await fetch('http://localhost:8000/api/auth/me/', {
    credentials: 'include'
  });
  return response.json();
};

// Refresh token (call when access token expires)
const refreshToken = async () => {
  const response = await fetch('http://localhost:8000/api/auth/refresh/', {
    method: 'POST',
    credentials: 'include'
  });
  return response.status === 200;
};

// Logout
const logout = async () => {
  const response = await fetch('http://localhost:8000/api/auth/logout/', {
    method: 'POST',
    credentials: 'include'
  });
  return response.json();
};

// Google OAuth
const googleLogin = async () => {
  // 1. Get authorization URL
  const urlResponse = await fetch('http://localhost:8000/api/auth/google/login/', {
    credentials: 'include'
  });
  const { authorization_url } = await urlResponse.json();
  
  // 2. Redirect user to Google
  window.location.href = authorization_url;
  
  // 3. After redirect back, get code from URL
  // const urlParams = new URLSearchParams(window.location.search);
  // const code = urlParams.get('code');
  
  // 4. Send code to backend
  // const authResponse = await fetch('http://localhost:8000/api/auth/google/', {
  //   method: 'POST',
  //   headers: { 'Content-Type': 'application/json' },
  //   credentials: 'include',
  //   body: JSON.stringify({ code })
  // });
};
```

### Axios Example

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/auth',
  withCredentials: true,  // Important for cookies!
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to handle 401 errors (token expired)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response.status === 401) {
      // Try to refresh token
      try {
        await api.post('/refresh/');
        // Retry original request
        return api(error.config);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
```

---

## 📝 Next Steps

### Ready for Frontend Implementation! ✅

The backend is complete and production-ready. You can now:

1. **Build the frontend UI** with:
   - Login form
   - Registration form
   - Google Sign In button
   - Protected routes
   - User profile display
   - Password change form

2. **Integrate the API** using:
   - JavaScript fetch API
   - Axios
   - React Query
   - SWR
   - Any HTTP client

3. **Add features like:**
   - Email verification
   - Password reset
   - 2FA / MFA
   - Social login (Facebook, GitHub, etc.)
   - User profile management
   - Avatar upload

---

## 📞 Support

For issues or questions:
1. Check [AUTHENTICATION_API.md](AUTHENTICATION_API.md) for detailed API docs
2. Review error messages in Django logs
3. Test with `test_auth.py` script
4. Verify environment variables are set correctly

---

**🎉 Congratulations! Your authentication system is ready to use!**

Let me know when you're ready to proceed with the frontend implementation! 🚀
