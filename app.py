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
import json
from io import StringIO, BytesIO
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['QUESTION_IMAGE_FOLDER'] = 'static/question_images'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['QUESTION_IMAGE_FOLDER'], exist_ok=True)

# --- Database Configuration ---
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///local.db')
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
    return render_template('admin_dashboard.html', 
                          questions=questions, 
                          submissions=submissions, 
                          all_users=all_users, 
                          classroom=classroom, 
                          meet_links=meet_links)

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

@app.route('/admin/edit-question/<int:question_id>', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    q = Question.query.get_or_404(question_id)
    if request.method == 'POST':
        q.text = request.form.get('text')
        q.topic = request.form.get('topic')
        q.option_a = request.form.get('option_a')
        q.option_b = request.form.get('option_b')
        q.option_c = request.form.get('option_c')
        q.option_d = request.form.get('option_d')
        q.correct_answer = request.form.get('correct_answer')
        q.explanation = request.form.get('explanation')
        q.time_limit = request.form.get('time_limit', type=int)
        db.session.commit()
        flash('Question updated!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('edit_question.html', q=q)

@app.route('/admin/delete-question/<int:question_id>', methods=['POST'])
@login_required
def delete_question(question_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    q = Question.query.get_or_404(question_id)
    db.session.delete(q)
    db.session.commit()
    flash('Question deleted!', 'info')
    return redirect(url_for('admin_questions_dashboard'))

@app.route('/admin/update-classroom', methods=['POST'])
@login_required
def update_classroom():
    if current_user.role != 'admin': return redirect(url_for('index'))
    link = request.form.get('meet_link')
    is_live = 'is_live' in request.form
    classroom = Classroom.query.first()
    if not classroom:
        classroom = Classroom(active_meet_link=link, is_live=is_live)
        db.session.add(classroom)
    else:
        classroom.active_meet_link = link
        classroom.is_live = is_live
        classroom.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Classroom updated!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add-meet-link', methods=['POST'])
@login_required
def add_meet_link():
    if current_user.role != 'admin': return redirect(url_for('index'))
    label = request.form.get('label')
    url = request.form.get('url')
    new_link = MeetLink(label=label, url=url)
    db.session.add(new_link)
    db.session.commit()
    flash('Meeting link added!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle-meet-link/<int:link_id>', methods=['POST'])
@login_required
def toggle_meet_link(link_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    link = MeetLink.query.get_or_404(link_id)
    link.is_active = not link.is_active
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-meet-link/<int:link_id>', methods=['POST'])
@login_required
def delete_meet_link(link_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    link = MeetLink.query.get_or_404(link_id)
    db.session.delete(link)
    db.session.commit()
    flash('Meeting link deleted!', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/refresh-classroom')
@login_required
def refresh_classroom():
    flash('Classroom link refreshed!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/questions')
@login_required
def admin_questions_dashboard():
    if current_user.role != 'admin': return redirect(url_for('index'))
    questions = Question.query.order_by(Question.created_at.desc()).all()
    return render_template('admin_questions.html', active_questions=questions)

@app.route('/admin/submissions')
@login_required
def admin_submissions_dashboard():
    if current_user.role != 'admin': return redirect(url_for('index'))
    submissions = Answer.query.order_by(Answer.submitted_at.desc()).all()
    return render_template('admin_submissions.html', results=submissions)

@app.route('/admin/members')
@login_required
def admin_members_dashboard():
    if current_user.role != 'admin': return redirect(url_for('index'))
    members = User.query.filter_by(role='student').all()
    return render_template('admin_members.html', all_users=members)

@app.route('/admin/export-members')
@login_required
def export_members():
    if current_user.role != 'admin': return redirect(url_for('index'))
    members = User.query.filter_by(role='student').all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Full Name', 'Username', 'Registration Date'])
    for m in members:
        cw.writerow([m.full_name, m.username, m.created_at])
    output = si.getvalue()
    return send_file(BytesIO(output.encode()), mimetype='text/csv', as_attachment=True, download_name='members.csv')

@app.route('/admin/export-submissions')
@login_required
def export_submissions():
    if current_user.role != 'admin': return redirect(url_for('index'))
    submissions = Answer.query.all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Student', 'Question', 'Outcome', 'Timestamp'])
    for s in submissions:
        cw.writerow([s.student.full_name, s.question.text[:50], 'PASS' if s.is_correct else 'FAIL', s.submitted_at])
    output = si.getvalue()
    return send_file(BytesIO(output.encode()), mimetype='text/csv', as_attachment=True, download_name='submissions.csv')

@app.route('/download/<filename>')
@login_required
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/admin/notifications')
@login_required
def get_notifications():
    if current_user.role != 'admin': return jsonify({'count': 0, 'notifications': []})
    notifs = Notification.query.filter_by(read=False).order_by(Notification.created_at.desc()).limit(20).all()
    notif_list = [{
        'student_name': n.student_name,
        'question_text': n.question_text or 'Question',
        'is_correct': n.is_correct,
        'created_at': n.created_at.strftime('%H:%M')
    } for n in notifs]
    return jsonify({'count': len(notifs), 'notifications': notif_list})

@app.route('/admin/notifications/mark_read', methods=['POST'])
@login_required
def mark_notifications_read():
    if current_user.role != 'admin': return jsonify({'status': 'ok'})
    Notification.query.filter_by(read=False).update({Notification.read: True})
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    today = datetime.utcnow().date()
    questions = Question.query.order_by(Question.created_at.desc()).all()
    answers = Answer.query.filter_by(student_id=current_user.id).all()
    user_answers = {a.question_id: a for a in answers}
    
    attempts = Attempt.query.filter_by(student_id=current_user.id).all()
    user_attempts = {at.question_id: at.start_time.timestamp() * 1000 for at in attempts}
    
    classroom = Classroom.query.first()
    active_meet_links = MeetLink.query.filter_by(is_active=True).all()
    
    stats = {
        'solved': len(answers),
        'correct': sum(1 for a in answers if a.is_correct),
        'incorrect': sum(1 for a in answers if not a.is_correct),
        'accuracy': (sum(1 for a in answers if a.is_correct) / len(answers) * 100) if answers else 0,
        'today_solved': sum(1 for a in answers if a.submitted_at.date() == today),
        'today_total': Question.query.filter(db.func.date(Question.created_at) == today).count(),
        'today_remaining': 0
    }
    stats['today_remaining'] = max(0, stats['today_total'] - stats['today_solved'])
    
    return render_template('student_dashboard.html', 
                          questions=questions, 
                          user_answers=user_answers, 
                          user_attempts=user_attempts, 
                          classroom=classroom,
                          active_meet_links=active_meet_links,
                          stats=stats,
                          server_now=datetime.utcnow().timestamp() * 1000)

@app.route('/student/start_attempt', methods=['POST'])
@login_required
def student_start_attempt():
    data = request.get_json()
    question_id = data.get('question_id')
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
    
    file_path = None
    if 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            file_path = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_path))
    
    answer = Answer(student_id=current_user.id, question_id=q_id, selected_option=ans, is_correct=is_correct, file_path=file_path)
    db.session.add(answer)
    
    notif = Notification(
        message=f"Submission from {current_user.full_name}", 
        type='submission', 
        student_id=current_user.id, 
        student_name=current_user.full_name, 
        question_id=q_id, 
        question_text=q.text[:50],
        is_correct=is_correct
    )
    db.session.add(notif)
    
    db.session.commit()
    return jsonify({'status': 'success', 'is_correct': is_correct})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
