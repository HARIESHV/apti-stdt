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
   - **Start Command**: `python app.py`
   - **Instance Type**: Free

5. **Environment Variables (CRITICAL)**:
   - Click **"Advanced"** → **"Add Environment Variable"**
   - **`SECRET_KEY`**: a long random string
   - **`MONGO_URI`**: Your MongoDB Atlas Connection String

6. Click **"Create Web Service"**

### Step 3: Access Your App
- Render will provide a URL like: `https://aptitudepro.onrender.com`
- Share this URL with anyone worldwide! 🌍

## ⚠️ Important Notes

### Database Persistence
- **Current Setup**: This website uses **MongoDB**.
- **Issue**: `localhost:27017` only works on your own computer.
- **Solution**: Use **MongoDB Atlas** (Free Tier) for hosting your data in the cloud.
  1. Create a free cluster at [mongodb.com](https://www.mongodb.com/cloud/atlas).
  2. Whitelist all IPs (`0.0.0.0/0`) in the Atlas Network Access tab.
  3. Copy your Connection String and add it to Render as an Environment Variable named `MONGO_URI`.

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
- **Admin**: username: `admin`, password: `adminpassword`
- **Students**: Register via `/register` route

## 📞 Support
For issues, check the deployment logs on your hosting platform.
