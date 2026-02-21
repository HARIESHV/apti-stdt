# 🚀 AptitudePro - Firebase Edition 🛰️

AptitudePro is a robust, full-stack aptitude quiz platform featuring dedicated student and administrator portals. It is now powered by **Firebase Firestore** for real-time data management.

## 📂 Project Architecture
```text
apti-stdt/
├── app.py              # Main Application (Flask)
├── requirements.txt    # Dependencies
├── static/             # Assets (CSS, Images)
└── templates/          # HTML Templates (Jinja2)
```

## ✨ Features
- **Role-Based Access**: Separate dashboards for Admins and Students.
- **Real-time Database**: Powered by Google Firebase Firestore.
- **Admin Control**: Live classroom management, question posting with images, and instant notifications.
- **Responsive Design**: Premium, glassmorphism-based UI for mobile and desktop.

## 🛠️ Local Setup
1. **Prerequisites**: Python 3.x and Firebase Account.
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Firebase**:
   - Download your `serviceAccountKey.json` from Firebase Console.
   - Place it in the project root folder.
4. **Configure Environment**:
   Create a `.env` file:
   ```env
   SECRET_KEY=your_secret_key
   FIREBASE_SERVICE_ACCOUNT_JSON=serviceAccountKey.json
   ```
5. **Initialize Admin**:
   Run the app:
   ```bash
   python app.py
   ```
   Visit `http://localhost:5000/init-admin` to set up the first admin.

6. **Access**: `http://localhost:5000`

## 🎯 Default Admin Credentials
- **Username**: `admin`
- **Password**: `admin123`

## 📞 Support
For issues or feature requests, contact the developer team.
