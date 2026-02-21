# 🚀 AptitudePro - Zero-Config Edition 📦

AptitudePro is a full-stack aptitude quiz platform. It is now powered by **SQLite** for the simplest possible setup—no external servers or passwords required.

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
- **Zero-Config**: No need for MySQL, PostgreSQL, or Firebase.
- **Portable**: Database is stored in a local file called `local.db`.
- **Admin Dashboard**: Full control over questions and classrooms.
- **Easy Deployment**: Works instantly on Render without environment variables.

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

## 🌍 Render Deployment
Just push and deploy! No `DATABASE_URL` environment variables are needed for SQLite.

## 🎯 Default Admin Credentials
- **Username**: `admin`
- **Password**: `admin123`
