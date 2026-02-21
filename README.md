# 🚀 AptitudePro - Premium Quiz Platform

AptitudePro is a full-stack aptitude quiz platform featuring dedicated student and administrator portals. It supports **MySQL** for local development and **PostgreSQL** for cloud deployment (Render).

## 📂 Project Architecture
```text
apti-stdt/
├── app.py              # Main Application (Flask)
├── models.py           # Database Schema (SQLAlchemy)
├── init_db.py          # DB Initialization Script
├── requirements.txt    # Dependencies
├── static/             # Assets (CSS, Images)
└── templates/          # HTML Templates (Jinja2)
```

## ✨ Features
- **Role-Based Access**: Separate dashboards for Admins and Students.
- **SQL Backend**: Powered by SQLAlchemy ORM.
- **Hybrid Database**: Automatic switching between MySQL and PostgreSQL.
- **Admin Control**: Live classroom management, question posting with images, and instant notifications.

## 🛠️ Local Setup
1. **Prerequisites**: Python 3.x and MySQL.
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment**:
   Create a `.env` file:
   ```env
   SECRET_KEY=your_secret_key
   DATABASE_URL=mysql+pymysql://root:@localhost:3306/aptipro
   ```
4. **Initialize Database**:
   ```bash
   python init_db.py
   ```
5. **Run App**:
   ```bash
   python app.py
   ```

## 🎯 Default Admin Credentials
- **Username**: `admin`
- **Password**: `admin123`
