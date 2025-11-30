# 🚀 Render Deployment Guide for GitHub Bot

## 📋 Prerequisites

- [x] GitHub repository created: `https://github.com/nishantb66/CODE-bot`
- [ ] Render account (free tier available at https://render.com)
- [ ] MongoDB Atlas account (free tier)
- [ ] Groq API Key
- [ ] GitHub Personal Access Token

---

## 🔧 Step 1: Prepare Your Project

### 1.1 Create `build.sh` (Render build script)

Create a file named `build.sh` in your project root:

```bash
#!/usr/bin/env bash
# exit on error
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
```

Make it executable:
```bash
chmod +x build.sh
```

### 1.2 Update `requirements.txt`

Add these production dependencies:

```txt
Django>=5.0.0,<6.0.0
python-dotenv>=1.0.0
Jinja2>=3.1.0
djangorestframework>=3.14.0
pymongo>=4.6.0
groq>=0.4.0
requests>=2.31.0
gunicorn>=21.2.0
whitenoise>=6.6.0
```

### 1.3 Update `settings.py`

Add WhiteNoise middleware for static files (already at line 44):

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add this line
    'django.contrib.sessions.middleware.SessionMiddleware',
    # ... rest of middleware
]

# Static files configuration
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

---

## 🌐 Step 2: Set Up MongoDB Atlas (Free Tier)

1. **Create MongoDB Atlas Account:**
   - Go to https://www.mongodb.com/cloud/atlas/register
   - Sign up for free

2. **Create a Free Cluster:**
   - Choose **M0 Sandbox** (Free tier: 512MB storage)
   - Select a cloud provider and region (closest to your users)
   - Cluster name: `github-bot-cluster`

3. **Create Database User:**
   - Go to **Database Access**
   - Click **Add New Database User**
   - Username: `github_bot_user`
   - Password: Generate a strong password (save it!)
   - Database User Privileges: **Read and write to any database**

4. **Whitelist IP Addresses:**
   - Go to **Network Access**
   - Click **Add IP Address**
   - Click **Allow Access from Anywhere** (0.0.0.0/0)
   - This is needed for Render to connect

5. **Get Connection String:**
   - Go to **Database** → **Connect**
   - Choose **Connect your application**
   - Copy the connection string:
   ```
   mongodb+srv://github_bot_user:<password>@github-bot-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
   - Replace `<password>` with your actual password

---

## 🎯 Step 3: Deploy to Render

### 3.1 Create Web Service

1. **Go to Render Dashboard:**
   - Visit https://dashboard.render.com
   - Click **New +** → **Web Service**

2. **Connect GitHub Repository:**
   - Click **Connect account** (if not connected)
   - Select your repository: `nishantb66/CODE-bot`
   - Click **Connect**

3. **Configure Web Service:**

   | Setting | Value |
   |---------|-------|
   | **Name** | `github-bot` or `code-bot` |
   | **Region** | Choose closest to you |
   | **Branch** | `main` |
   | **Root Directory** | Leave empty |
   | **Runtime** | `Python 3` |
   | **Build Command** | `./build.sh` |
   | **Start Command** | `gunicorn analyzer.wsgi:application` |
   | **Instance Type** | `Free` |

### 3.2 Add Environment Variables

Click **Advanced** → **Add Environment Variable** and add these:

| Key | Value | Notes |
|-----|-------|-------|
| `PYTHON_VERSION` | `3.11.0` | Python version |
| `SECRET_KEY` | `<generate-random-string>` | Use https://djecrety.ir/ |
| `DEBUG` | `False` | **IMPORTANT: Set to False in production** |
| `ALLOWED_HOSTS` | `.onrender.com,localhost,127.0.0.1` | Your Render domain |
| `GITHUB_PAT` | `ghp_xxxxxxxxxxxxx` | Your GitHub Personal Access Token |
| `GROQ_API_KEY` | `gsk_xxxxxxxxxxxxx` | Your Groq API Key |
| `MONGODB_URI` | `mongodb+srv://...` | Your MongoDB Atlas connection string |

**To generate a secure SECRET_KEY:**
```python
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### 3.3 Deploy

1. Click **Create Web Service**
2. Render will automatically:
   - Clone your repository
   - Run `build.sh`
   - Install dependencies
   - Collect static files
   - Start your application

3. **Monitor the deployment:**
   - Watch the logs in real-time
   - First deployment takes 5-10 minutes

---

## 🔍 Step 4: Verify Deployment

### 4.1 Check Your App

Your app will be available at:
```
https://your-app-name.onrender.com
```

### 4.2 Test Endpoints

```bash
# Test health check
curl https://your-app-name.onrender.com/

# Test API
curl -X POST https://your-app-name.onrender.com/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello!", "model_id": 2}'
```

---

## 📊 Free Tier Limits

| Service | Free Tier | Limits |
|---------|-----------|--------|
| **Render** | 750 hours/month | Spins down after 15 min inactivity |
| **MongoDB Atlas** | 512MB storage | Shared cluster |
| **Groq API** | 14,400 requests/day | Rate limited |
| **GitHub API** | 5,000 requests/hour | Per user |

---

## ⚠️ Important Notes

### Cold Starts
- **Free tier apps spin down after 15 minutes of inactivity**
- First request after spin-down takes 30-60 seconds
- Solution: Use a service like [UptimeRobot](https://uptimerobot.com/) to ping your app every 14 minutes

### Static Files
- WhiteNoise serves static files efficiently
- No need for separate CDN on free tier

### Database
- SQLite is NOT recommended for Render (ephemeral filesystem)
- Use MongoDB Atlas for persistent storage
- Consider migrating Django models to MongoDB if needed

### Environment Variables
- **NEVER** commit `.env` to GitHub
- Always use Render's environment variables for production
- Keep sensitive keys secure

---

## 🔄 Update Your Deployment

### When you push changes to GitHub:

```bash
git add .
git commit -m "Your commit message"
git push origin main
```

Render will **automatically redeploy** your app! 🎉

### Manual Redeploy:
- Go to Render Dashboard
- Click your service
- Click **Manual Deploy** → **Deploy latest commit**

---

## 🐛 Troubleshooting

### Issue: Build Failed
**Solution:** Check the build logs in Render dashboard
- Ensure `build.sh` is executable
- Verify all dependencies in `requirements.txt`

### Issue: App Crashes on Start
**Solution:** Check the logs
```bash
# In Render dashboard, go to Logs tab
```
Common causes:
- Missing environment variables
- MongoDB connection issues
- Invalid `ALLOWED_HOSTS`

### Issue: Static Files Not Loading
**Solution:** 
1. Ensure WhiteNoise is installed
2. Run `python manage.py collectstatic`
3. Check `STATIC_ROOT` and `STATIC_URL` settings

### Issue: MongoDB Connection Failed
**Solution:**
1. Verify connection string is correct
2. Check MongoDB Atlas IP whitelist (should include 0.0.0.0/0)
3. Verify database user credentials

---

## 📈 Monitoring

### Render Dashboard
- **Metrics:** CPU, Memory, Response time
- **Logs:** Real-time application logs
- **Events:** Deployment history

### MongoDB Atlas
- **Metrics:** Database operations, storage usage
- **Performance:** Query performance insights

---

## 🚀 Next Steps

1. **Custom Domain** (optional):
   - Add your custom domain in Render settings
   - Update `ALLOWED_HOSTS` to include your domain

2. **SSL Certificate:**
   - Render provides free SSL automatically
   - Your app will be available via HTTPS

3. **Monitoring:**
   - Set up UptimeRobot for uptime monitoring
   - Configure error tracking (e.g., Sentry)

4. **CI/CD:**
   - Already set up! Push to `main` = auto-deploy

---

## 📞 Support

- **Render Docs:** https://render.com/docs
- **MongoDB Atlas Docs:** https://docs.atlas.mongodb.com/
- **Django Deployment:** https://docs.djangoproject.com/en/5.0/howto/deployment/

---

**Your app is now live and accessible to the world! 🌍**

**Live URL:** `https://your-app-name.onrender.com`
