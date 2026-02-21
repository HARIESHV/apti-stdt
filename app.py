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

# Import meet_utils if available
try:
    from meet_utils import get_meet_info
except ImportError:
    def get_meet_info(url):
        return ("Classroom", None)

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['QUESTION_IMAGE_FOLDER'] = 'static/question_images'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

# --- Database Configuration ---
# --- Database Configuration ---
DATABASE_URL = os.environ.get('DATABASE_URL')

# Debugging
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL is not set!")
else:
    # Normalize for SQLAlchemy 1.4+ / 2.0+
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+psycopg2://', 1)
    elif DATABASE_URL.startswith('postgresql://'):
        DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://', 1)
    elif DATABASE_URL.startswith('mysql://'):
        DATABASE_URL = DATABASE_URL.replace('mysql://', 'mysql+pymysql://', 1)
    
    # Render PostgreSQL often requires SSL
    if 'postgresql' in DATABASE_URL and 'sslmode' not in DATABASE_URL:
        if '?' in DATABASE_URL:
            DATABASE_URL += '&sslmode=require'
        else:
            DATABASE_URL += '?sslmode=require'
            
    print(f"✅ Database connected: {DATABASE_URL.split(':')[0]}")

if not DATABASE_URL:
    # Use a fallback for local dev if .env failed
    DATABASE_URL = 'mysql+pymysql://root:@localhost:3306/aptipro'
    print("⚠️ Using local fallback MySQL URL")

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from models import db, User, Question, Answer, Attempt, Classroom, MeetLink, Notification

db.init_app(app)
migrate = Migrate(app, db)

# --- Initialization ---
def init_db():
    with app.app_context():
        db.create_all()
        try:
            # Initialize Classroom row if missing
            if not Classroom.query.first():
                db.session.add(Classroom(
                    active_meet_link='https://meet.google.com/',
                    detected_title='Official Classroom',
                    is_live=False,
                    updated_at=datetime.utcnow()
                ))
                db.session.commit()

            # Create default admin if none exists
            if not User.query.filter_by(role='admin').first():
                admin = User(
                    username='admin',
                    full_name='Administrator',
                    password=generate_password_hash('admin123'),
                    role='admin',
                    created_at=datetime.utcnow()
                )
                db.session.add(admin)
                db.session.commit()
                print("Default admin created: admin / admin123")
        except Exception as e:
            db.session.rollback()
            print(f"⚠️ DATABASE ERROR during init: {e}")

# init_db()  # Commented out to prevent crashes on Render. Run manually or via CLI.

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['QUESTION_IMAGE_FOLDER'], exist_ok=True)

# --- Helpers ---

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_meet_link(url):
    if not url: return True
    return any(domain in url.lower() for domain in ['meet.google.com/', 'meet.new/'])

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        full_name = request.form.get('full_name')
        password = request.form.get('password')

        max_members = 500
        current_members = User.query.filter_by(role='student').count()
        if current_members >= max_members:
            flash(f'Registration limit reached ({max_members} members).')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))

        new_user = User(
            username=username,
            full_name=full_name,
            password=generate_password_hash(password),
            role='student',
            created_at=datetime.utcnow()
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        flash('Account created!')
        return redirect(url_for('student_dashboard'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Admin Routes ---

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))

    questions = Question.query.order_by(Question.created_at.desc()).all()
    submissions = Answer.query.order_by(Answer.submitted_at.desc()).limit(10).all()
    all_users = User.query.filter_by(role='student').all()
    classroom = Classroom.query.first()
    meet_links = MeetLink.query.order_by(MeetLink.created_at.desc()).all()

    return render_template('admin_dashboard.html',
                           questions=questions,
                           members=all_users[:8],
                           results=submissions,
                           classroom=classroom,
                           meet_links=meet_links,
                           all_users=all_users)

@app.route('/admin/questions')
@login_required
def admin_questions_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))
    questions = Question.query.order_by(Question.created_at.desc()).all()
    return render_template('admin_questions.html', active_questions=questions, expired_questions=[])

@app.route('/admin/submissions')
@login_required
def admin_submissions_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))
    submissions = Answer.query.order_by(Answer.submitted_at.desc()).all()
    return render_template('admin_submissions.html', results=submissions)

@app.route('/admin/members')
@login_required
def admin_members_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))
    members = User.query.filter_by(role='student').all()
    return render_template('admin_members.html', all_users=members)

@app.route('/admin/post_question', methods=['GET', 'POST'])
@login_required
def post_question():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))
    if request.method == 'GET':
        return render_template('post_question.html')

    image = request.files.get('image')
    image_filename = None
    if image and allowed_file(image.filename):
        image_filename = secure_filename(f"q_{datetime.now().timestamp()}_{image.filename}")
        image.save(os.path.join(app.config['QUESTION_IMAGE_FOLDER'], image_filename))

    q = Question(
        text=request.form.get('text'),
        topic=request.form.get('topic', ''),
        option_a=request.form.get('option_a'),
        option_b=request.form.get('option_b'),
        option_c=request.form.get('option_c'),
        option_d=request.form.get('option_d'),
        correct_answer=request.form.get('correct_answer'),
        explanation=request.form.get('explanation'),
        meet_link=request.form.get('meet_link'),
        time_limit=request.form.get('time_limit', 10, type=int),
        image_file=image_filename,
        created_at=datetime.utcnow()
    )
    db.session.add(q)
    db.session.commit()
    flash('Question posted!')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_question/<int:question_id>', methods=['POST', 'GET'])
@login_required
def delete_question(question_id):
    if current_user.role == 'admin':
        q = Question.query.get_or_404(question_id)
        db.session.delete(q)
        db.session.commit()
        flash('Question deleted')
    return redirect(url_for('admin_questions_dashboard'))

@app.route('/admin/edit_question/<int:question_id>', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))

    q = Question.query.get_or_404(question_id)

    if request.method == 'POST':
        q.text = request.form.get('text')
        q.topic = request.form.get('topic', '')
        q.option_a = request.form.get('option_a')
        q.option_b = request.form.get('option_b')
        q.option_c = request.form.get('option_c')
        q.option_d = request.form.get('option_d')
        q.correct_answer = request.form.get('correct_answer')
        q.explanation = request.form.get('explanation')
        q.time_limit = request.form.get('time_limit', 10, type=int)

        image = request.files.get('image')
        if image and image.filename:
            image_filename = secure_filename(f"q_{datetime.now().timestamp()}_{image.filename}")
            image.save(os.path.join(app.config['QUESTION_IMAGE_FOLDER'], image_filename))
            q.image_file = image_filename

        db.session.commit()
        flash('Question updated!')
        return redirect(url_for('admin_questions_dashboard'))

    return render_template('edit_question.html', q=q)

# --- Classroom / Meet Link Routes ---

@app.route('/admin/update_classroom', methods=['POST'])
@login_required
def update_classroom():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))
    link = request.form.get('meet_link')
    is_live = 'is_live' in request.form
    title, _ = get_meet_info(link) if link else ("Classroom", None)

    classroom = Classroom.query.first()
    if classroom:
        classroom.active_meet_link = link
        classroom.is_live = is_live
        classroom.detected_title = title
        classroom.updated_at = datetime.utcnow()
        db.session.commit()
    flash('Classroom updated')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/refresh_classroom')
@login_required
def refresh_classroom():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))
    classroom = Classroom.query.first()
    if classroom and classroom.active_meet_link:
        title, _ = get_meet_info(classroom.active_meet_link)
        classroom.detected_title = title
        db.session.commit()
        flash('Status refreshed')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_meet_link', methods=['POST'])
@login_required
def add_meet_link():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))
    label = request.form.get('label')
    url = request.form.get('url')
    if is_valid_meet_link(url):
        db.session.add(MeetLink(label=label, url=url, is_active=True, created_at=datetime.utcnow()))
        db.session.commit()
        flash('Link added')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle_meet_link/<int:link_id>', methods=['POST', 'GET'])
@login_required
def toggle_meet_link(link_id):
    if current_user.role == 'admin':
        link = MeetLink.query.get_or_404(link_id)
        link.is_active = not link.is_active
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_meet_link/<int:link_id>', methods=['POST', 'GET'])
@login_required
def delete_meet_link(link_id):
    if current_user.role == 'admin':
        link = MeetLink.query.get_or_404(link_id)
        db.session.delete(link)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

# --- Student Routes ---

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('admin_dashboard'))

    questions = Question.query.order_by(Question.created_at.desc()).all()
    answers_list = Answer.query.filter_by(student_id=current_user.id).all()
    user_answers = {str(a.question_id): a for a in answers_list}
    attempts_list = Attempt.query.filter_by(student_id=current_user.id).all()
    user_attempts = {str(a.question_id): a.start_time.timestamp() * 1000 for a in attempts_list}

    correct_count = sum(1 for a in answers_list if a.is_correct)

    today_utc_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_questions = [q for q in questions if q.created_at and q.created_at >= today_utc_start]
    today_question_ids = {str(q.id) for q in today_questions}
    today_answers = [a for a in answers_list if str(a.question_id) in today_question_ids]

    stats = {
        'total': len(questions),
        'solved': len(user_answers),
        'unsolved': len(questions) - len(user_answers),
        'correct': correct_count,
        'incorrect': len(user_answers) - correct_count,
        'accuracy': (correct_count / len(user_answers) * 100) if user_answers else 0,
        'today_total': len(today_questions),
        'today_solved': len(today_answers),
        'today_remaining': max(0, len(today_questions) - len(today_answers))
    }

    classroom = Classroom.query.first()
    active_meet_links = MeetLink.query.filter_by(is_active=True).all()

    return render_template('student_dashboard.html',
                           questions=questions, user_answers=user_answers,
                           user_attempts=user_attempts, stats=stats,
                           classroom=classroom, active_meet_links=active_meet_links,
                           daily_stats=[],
                           server_now=datetime.utcnow().timestamp() * 1000)

@app.route('/student/start_attempt', methods=['POST'])
@login_required
def start_attempt():
    question_id = request.json.get('question_id')
    existing = Attempt.query.filter_by(student_id=current_user.id, question_id=int(question_id)).first()
    if not existing:
        start_time = datetime.utcnow()
        attempt = Attempt(student_id=current_user.id, question_id=int(question_id), start_time=start_time)
        db.session.add(attempt)
        db.session.commit()
        return jsonify({'start_time': start_time.timestamp() * 1000})
    return jsonify({'start_time': existing.start_time.timestamp() * 1000})

@app.route('/student/submit_answer', methods=['POST'])
@login_required
def submit_answer():
    question_id = int(request.form.get('question_id'))
    selected_option = request.form.get('selected_option')
    file = request.files.get('file')
    q = Question.query.get(question_id)
    if not q:
        return redirect(url_for('student_dashboard'))

    # Time limit enforcement
    if q.time_limit and q.time_limit > 0:
        attempt = Attempt.query.filter_by(student_id=current_user.id, question_id=question_id).first()
        if attempt:
            expiry_time = attempt.start_time + timedelta(minutes=q.time_limit)
            if datetime.utcnow() > expiry_time:
                flash('TIME EXPIRED: Your submission was recorded as late.')
                db.session.add(Answer(
                    student_id=current_user.id,
                    question_id=question_id,
                    selected_option=selected_option,
                    file_path=None,
                    is_correct=False,
                    is_expired=True,
                    submitted_at=datetime.utcnow()
                ))
                db.session.commit()
                return redirect(url_for('student_dashboard'))

    filename = None
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{current_user.username}_{datetime.now().timestamp()}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    is_correct = (selected_option == q.correct_answer) if selected_option else None
    db.session.add(Answer(
        student_id=current_user.id,
        question_id=question_id,
        selected_option=selected_option,
        file_path=filename,
        is_correct=is_correct,
        submitted_at=datetime.utcnow()
    ))

    # Notify admin
    q_text = q.text or ''
    db.session.add(Notification(
        type='submission',
        student_id=current_user.id,
        student_name=current_user.full_name or current_user.username,
        question_id=question_id,
        question_text=(q_text[:80] + '...') if len(q_text) > 80 else q_text,
        is_correct=is_correct,
        read=False,
        created_at=datetime.utcnow()
    ))
    db.session.commit()

    flash('Submitted!')
    return redirect(url_for('student_dashboard'))

# --- Notification Routes ---

@app.route('/admin/notifications')
@login_required
def get_notifications():
    if current_user.role != 'admin':
        return jsonify({'error': 'Forbidden'}), 403
    notifs = Notification.query.filter_by(read=False).order_by(Notification.created_at.desc()).limit(20).all()
    result = [{
        'id': n.id,
        'student_name': n.student_name or 'Unknown',
        'question_text': n.question_text or '',
        'is_correct': n.is_correct,
        'created_at': n.created_at.strftime('%H:%M') if n.created_at else ''
    } for n in notifs]
    return jsonify({'notifications': result, 'count': len(result)})

@app.route('/admin/notifications/mark_read', methods=['POST'])
@login_required
def mark_notifications_read():
    if current_user.role != 'admin':
        return jsonify({'error': 'Forbidden'}), 403
    Notification.query.filter_by(read=False).update({'read': True})
    db.session.commit()
    return jsonify({'ok': True})

# --- Export Routes ---

@app.route('/admin/export/submissions')
@login_required
def export_submissions():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))
    answers = Answer.query.order_by(Answer.submitted_at.desc()).all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student Name', 'Username', 'Question', 'Result', 'Submitted At'])
    for ans in answers:
        student = ans.student
        q = ans.question
        writer.writerow([
            student.full_name if student else 'Deleted User',
            student.username if student else 'N/A',
            (q.text[:80] + '...') if q and len(q.text) > 80 else (q.text if q else 'Deleted Question'),
            'PASS' if ans.is_correct else 'FAIL',
            ans.submitted_at.strftime('%Y-%m-%d %H:%M') if ans.submitted_at else 'N/A'
        ])
    output.seek(0)
    return send_file(
        BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'submissions_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
    )

@app.route('/admin/export/members')
@login_required
def export_members():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))
    users = User.query.filter_by(role='student').all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Full Name', 'Username', 'Role', 'Registration Date'])
    for user in users:
        writer.writerow([
            user.full_name or 'N/A',
            user.username,
            user.role.upper(),
            user.created_at.strftime('%Y-%m-%d') if user.created_at else 'Legacy Record'
        ])
    output.seek(0)
    return send_file(
        BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'members_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
    )

@app.route('/download/<filename>')
@login_required
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    # Use the PORT environment variable provided by Render, default to 5000 for local dev
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Server starting on port {port}...")
    # Bind to 0.0.0.0 to make it accessible externally
    app.run(host="0.0.0.0", port=port)
