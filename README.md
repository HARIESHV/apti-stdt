# 🚀 AptitudePro Localhost Setup Guide

This project is a simple, database-free aptitude website designed to run on your local machine (localhost).

## 📂 Folder Structure
```text
apti-stdt/
├── app.py              # Backend logic (Python/Flask)
├── questions.json       # Questions organized by level
├── requirements.txt     # Necessary libraries
├── static/
│   └── css/
│       └── style.css    # Premium modern design
└── templates/
    ├── index.html       # Landing page (Name Entry)
    ├── quiz.html        # Question display
    └── result.html      # Score & Results
```

## 🛠️ Requirements
- **Python 3.x** installed on your system.
- **Flask** library.

## 🏃 How to Run on Localhost

### Option 1: Using Python (Native Localhost)
1. Open your terminal or command prompt in the `apti-stdt` folder.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the server:
   ```bash
   python app.py
   ```
4. Open your browser and go to: `http://127.0.0.1:5000`

### Option 2: Using Node.js (Alternative)
If you prefer Node.js, you can use any static server, but since this app uses Python/Flask for session management, it is recommended to keep it as a Python app. If you need a Node version, I can provide an Express.js equivalent.

## ✨ Features
- **No Database**: All data is stored in `JSON` and `Session`.
- **Level System**: Questions progress as you answer them.
- **One Question at a Time**: Focused environment.
- **Validations**: Browsers and server-side checks ensure no empty usernames or skipped questions.
- **Responsive Design**: Works perfectly on mobile and desktop.
