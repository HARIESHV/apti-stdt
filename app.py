from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_file, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import secrets
import csv
from io import StringIO, BytesIO
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['QUESTION_IMAGE_FOLDER'] = 'static/question_images'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# --- Database Configuration ---
DATABASE_URL = os.environ.get('DATABASE_URL')
IS_RENDER = os.environ.get('RENDER')

if IS_RENDER and not DATABASE_URL:
    print("❌ WARNING: DATABASE_URL is not set in Render!")
    DATABASE_URL = "sqlite:///render_fallback.db"

if not DATABASE_URL:
    # Local fallback to MySQL
    DATABASE_URL = 'mysql+pymysql://root:@localhost:3306/aptipro'
    print("🏠 Local mode: Using MySQL")
else:
    # Normalizing database URL for SQLAlchemy
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+psycopg2://', 1)
    elif DATABASE_URL.startswith('postgresql://') and 'postgresql+psycopg2://' not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://', 1)
    
    if 'postgresql' in DATABASE_URL and 'sslmode' not in DATABASE_URL:
        DATABASE_URL += ('&' if '?' in DATABASE_URL else '?') + 'sslmode=require'

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from models import db, User, Question, Answer, Attempt, Classroom, MeetLink, Notification

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Helpers ---
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Routes ---
@app.route('/health')
def health():
    return jsonify({"status": "online", "database": DATABASE_URL.split(':')[0]})

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard' if current_user.role == 'admin' else 'student_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        full_name = request.form.get('full_name')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash('Username taken', 'warning')
            return redirect(url_for('register'))
        new_user = User(username=username, full_name=full_name, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        flash('Success!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin': return redirect(url_for('index'))
    questions = Question.query.order_by(Question.created_at.desc()).all()
    submissions = Answer.query.order_by(Answer.submitted_at.desc()).limit(10).all()
    all_users = User.query.filter_by(role='student').all()
    classroom = Classroom.query.first()
    meet_links = MeetLink.query.order_by(MeetLink.created_at.desc()).all()
    return render_template('admin_dashboard.html', questions=questions, submissions=submissions, all_users=all_users, classroom=classroom, meet_links=meet_links)

@app.route('/admin/post-question', methods=['GET', 'POST'])
@login_required
def post_question():
    if current_user.role != 'admin': return redirect(url_for('index'))
    if request.method == 'POST':
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                image_filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['QUESTION_IMAGE_FOLDER'], image_filename))
        
        q = Question(
            text=request.form.get('text'),
            topic=request.form.get('topic', 'General'),
            option_a=request.form.get('option_a'),
            option_b=request.form.get('option_b'),
            option_c=request.form.get('option_c'),
            option_d=request.form.get('option_d'),
            correct_answer=request.form.get('correct_answer'),
            explanation=request.form.get('explanation'),
            time_limit=request.form.get('time_limit', 10, type=int),
            image_file=image_filename
        )
        db.session.add(q)
        db.session.commit()
        flash('Question posted!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('post_question.html')

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    questions = Question.query.order_by(Question.created_at.desc()).all()
    answers = Answer.query.filter_by(student_id=current_user.id).all()
    user_answers = {a.question_id: a for a in answers}
    attempts = Attempt.query.filter_by(student_id=current_user.id).all()
    user_attempts = {at.question_id: at.start_time.timestamp() * 1000 for at in attempts}
    classroom = Classroom.query.first()
    return render_template('student_dashboard.html', questions=questions, user_answers=user_answers, user_attempts=user_attempts, classroom=classroom)

@app.route('/start_attempt/<int:question_id>')
@login_required
def start_attempt(question_id):
    attempt = Attempt.query.filter_by(student_id=current_user.id, question_id=question_id).first()
    if not attempt:
        attempt = Attempt(student_id=current_user.id, question_id=question_id)
        db.session.add(attempt)
        db.session.commit()
    return jsonify({'start_time': attempt.start_time.timestamp() * 1000})

@app.route('/submit_answer', methods=['POST'])
@login_required
def submit_answer():
    q_id = request.form.get('question_id', type=int)
    ans = request.form.get('selected_option')
    q = Question.query.get_or_404(q_id)
    is_correct = ans == q.correct_answer
    
    answer = Answer(student_id=current_user.id, question_id=q_id, selected_option=ans, is_correct=is_correct)
    db.session.add(answer)
    
    notif = Notification(message=f"Submission from {current_user.full_name}", type='submission', student_id=current_user.id, student_name=current_user.full_name, question_id=q_id, is_correct=is_correct)
    db.session.add(notif)
    
    db.session.commit()
    return jsonify({'status': 'success', 'is_correct': is_correct})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
