# 🚀 AptitudePro - Supabase Edition 🛰️

AptitudePro is a full-stack aptitude quiz platform powered by **Supabase (PostgreSQL)**.

## 📂 Project Architecture
```text
apti-stdt/
├── app.py              # Main Application (Flask)
├── models.py           # Database Schema (SQLAlchemy)
├── init_db.py          # Tables creation script
├── requirements.txt    # Dependencies
├── static/             # Assets (CSS, Images)
└── templates/          # HTML Templates (Jinja2)
```

## ✨ Features
- **Cloud Infrastructure**: Powered by Supabase's high-performance PostgreSQL.
- **Admin Dashboard**: Live management and student tracking.
- **Responsive UI**: Glassmorphism design for all devices.

## 🛠️ Supabase Setup
1. **Create Project**: Go to [Supabase](https://supabase.com/) and create a new project.
2. **Get Connection String**:
   - Go to **Project Settings** -> **Database**.
   - Copy the **Connection String** (Transaction or Session mode).
   - Ensure you replace `[YOUR-PASSWORD]` with your actual database password.
3. **Configure Environment**:
   Update your `.env` file:
   ```env
   SECRET_KEY=your_secret_key
   DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-ID].supabase.co:5432/postgres
   ```

## 🛠️ Local Installation
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Initialize Database**:
   ```bash
   python init_db.py
   ```
3. **Run App**:
   ```bash
   python app.py
   ```

## 🎯 Default Admin Credentials
- **Username**: `admin`
- **Password**: `admin123`
