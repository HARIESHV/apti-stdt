# 🚀 AptitudePro - Global Deployment Guide

## 📋 Overview
AptitudePro is a Flask-based aptitude quiz platform with separate portals for students and administrators.

## 🌍 Deploy to Render.com (Recommended)

### Step 1: Prepare Your Code
1. Make sure all files are committed to Git:
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   ```

2. Push to GitHub:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy on Render
1. Go to [render.com](https://render.com) and sign up/login
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `aptitudepro`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free

5. **Environment Variables (CRITICAL)**:
   - Click **"Advanced"** → **"Add Environment Variable"**
   - **`SECRET_KEY`**: a long random string
   - **`DATABASE_URL`**: Your PostgreSQL Connection String
     *(Example: `postgresql://user:password@host:5432/dbname`)*

6. Click **"Create Web Service"**

### Step 3: Access Your App
- Render will provide a URL like: `https://aptitudepro.onrender.com`
- Share this URL with anyone worldwide! 🌍

## ⚠️ Important Notes

### Database Persistence
- **Current Setup**: This website uses **SQL** (PostgreSQL in production, MySQL locally).
- **Issue**: `localhost` only works on your own computer.
- **Solution**: Use **Render PostgreSQL** (Free Tier).
  1. Click **New +** → **PostgreSQL** in Render.
  2. Copy the **Internal Database URL**.
  3. Add it to Render Web Service as an Environment Variable named `DATABASE_URL`.

### Initializing the Database (First-time setup)
When you first deploy to a new database, you need to create the tables:
1. Go to your Render Dashboard → Web Service → **Shell**.
2. Run the command: `python init_db.py`
3. This will create all tables and set up the default admin user.

### Security
- Change the `SECRET_KEY` in environment variables to a random string
- Change default admin password after first login (admin/adminpassword)

## 🔧 Alternative Deployment Options

### Railway.app
1. Go to [railway.app](https://railway.app)
2. Click "Start a New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway auto-detects Flask and deploys!

### PythonAnywhere
1. Go to [pythonanywhere.com](https://www.pythonanywhere.com)
2. Sign up for free account
3. Upload your code via Git or file upload
4. Configure WSGI file to point to your app
5. Set up virtual environment and install requirements

## 📱 Local Network Access (Already Working)
Your app is already configured for local network access:
- Run: `python app.py`
- Access from any device on your network: `http://YOUR_LOCAL_IP:5000`

## 🎯 Default Credentials
- **Admin**: username: `admin`, password: `admin123`
- **Students**: Register via `/register` route

## 📞 Support
For issues, check the deployment logs on your hosting platform.
