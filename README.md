# 🚀 AptitudePro - Premium Aptitude Platform

AptitudePro is a robust, full-stack aptitude quiz platform featuring dedicated student and administrator portals. It now supports high-performance SQL databases (MySQL and PostgreSQL).

## 📂 Project Architecture
```text
apti-stdt/
├── app.py              # Main Application (Flask)
├── models.py           # Database Schema (SQLAlchemy)
├── init_db.py          # Database Initialization Script
├── requirements.txt    # Dependencies
├── static/             # Assets (CSS, Images)
└── templates/          # HTML Templates (Jinja2)
```

## ✨ Features
- **Role-Based Access**: Separate dashboards for Admins and Students.
- **Hybrid Database**: Automatic switching between MySQL (Local) and PostgreSQL (Cloud).
- **Time Limits**: Questions can have per-student time restrictions.
- **Admin Control**: Live classroom management, question posting with images, and submission exports.
- **Real-time Notifications**: Admins get notified of student submissions.
- **Responsive Design**: Premium, glassmorphism-based UI for mobile and desktop.

## 🛠️ Local Setup
1. **Prerequisites**: Python 3.x and MySQL.
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment**:
   Create/Update `.env`:
   ```env
   SECRET_KEY=your_secret_key
   DATABASE_URL=mysql+pymysql://root:@localhost:3306/aptipro
   ```
4. **Initialize DB**:
   ```bash
   python init_db.py
   ```
5. **Run App**:
   ```bash
   python app.py
   ```
6. **Access**: `http://localhost:5000`

## 🌍 Deployment
Detailed deployment instructions for Render.com can be found in [DEPLOYMENT.md](DEPLOYMENT.md).

## 🎯 Default Admin Credentials
- **Username**: `admin`
- **Password**: `admin123`

## 📞 Support
For issues or feature requests, please contact the developer team.
