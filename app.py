from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_file, send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import secrets
import csv
import json
from io import StringIO, BytesIO
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, storage

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['QUESTION_IMAGE_FOLDER'] = 'static/question_images'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# --- Firebase Configuration ---
service_account_path = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON', 'serviceAccountKey.json')

if os.path.exists(service_account_path):
    cred = credentials.Certificate(service_account_path)
    firebase_admin.initialize_app(cred, {
        'storageBucket': os.environ.get('FIREBASE_STORAGE_BUCKET')
    })
    print("✅ Firebase initialized with service account.")
else:
    firebase_config = os.environ.get('FIREBASE_CONFIG_JSON')
    if firebase_config:
        config_dict = json.loads(firebase_config)
        cred = credentials.Certificate(config_dict)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized with environment config.")
    else:
        print("⚠️ WARNING: Firebase config not found. App running in restricted mode.")

db = firestore.client()

# --- User Class for Flask-Login ---
class User(UserMixin):
    def __init__(self, id, data):
        self.id = str(id)
        self.username = data.get('username')
        self.full_name = data.get('full_name')
        self.role = data.get('role', 'student')
        self.created_at = data.get('created_at')

    @staticmethod
    def get(user_id):
        doc = db.collection('users').document(str(user_id)).get()
        if doc.exists:
            return User(doc.id, doc.to_dict())
        return None

    @staticmethod
    def find_by_username(username):
        users = db.collection('users').where('username', '==', username).limit(1).stream()
        for user in users:
            return User(user.id, user.to_dict()), user.to_dict().get('password')
        return None, None

# --- Helpers ---
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def doc_to_dict(doc):
    if not doc or not doc.exists: return None
    d = doc.to_dict()
    d['id'] = doc.id
    # Convert timestamps to datetime objects for templates
    for k, v in d.items():
        if hasattr(v, 'timestamp') and not isinstance(v, (int, float, datetime)):
            # Handle potential Firestore timestamp
            try: d[k] = v.to_datetime()
            except: pass
    return d

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# --- Routes ---
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user, hashed_password = User.find_by_username(username)
        if user and check_password_hash(hashed_password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        full_name = request.form.get('full_name')
        password = request.form.get('password')
        
        user, _ = User.find_by_username(username)
        if user:
            flash('Username already exists', 'warning')
            return redirect(url_for('register'))
        
        db.collection('users').add({
            'username': username,
            'full_name': full_name,
            'password': generate_password_hash(password),
            'role': 'student',
            'created_at': datetime.utcnow()
        })
        flash('Registration successful!', 'success')
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
    questions = [doc_to_dict(q) for q in db.collection('questions').order_by('created_at', direction=firestore.Query.DESCENDING).stream()]
    submissions = [doc_to_dict(s) for s in db.collection('answers').order_by('submitted_at', direction=firestore.Query.DESCENDING).limit(10).stream()]
    all_users = [doc_to_dict(u) for u in db.collection('users').where('role', '==', 'student').stream()]
    
    classroom_doc = db.collection('classroom').document('main').get()
    classroom = doc_to_dict(classroom_doc)
    
    meet_links = [doc_to_dict(m) for m in db.collection('meet_links').order_by('created_at', direction=firestore.Query.DESCENDING).stream()]
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

        db.collection('questions').add({
            'text': request.form.get('text'),
            'topic': request.form.get('topic', 'General'),
            'option_a': request.form.get('option_a'),
            'option_b': request.form.get('option_b'),
            'option_c': request.form.get('option_c'),
            'option_d': request.form.get('option_d'),
            'correct_answer': request.form.get('correct_answer'),
            'explanation': request.form.get('explanation'),
            'meet_link': request.form.get('meet_link'),
            'time_limit': request.form.get('time_limit', 10, type=int),
            'image_file': image_filename,
            'created_at': datetime.utcnow()
        })
        flash('Question posted!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('post_question.html')

@app.route('/admin/edit-question/<q_id>', methods=['GET', 'POST'])
@login_required
def edit_question(q_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    doc_ref = db.collection('questions').document(q_id)
    if request.method == 'POST':
        doc_ref.update({
            'text': request.form.get('text'),
            'topic': request.form.get('topic'),
            'option_a': request.form.get('option_a'),
            'option_b': request.form.get('option_b'),
            'option_c': request.form.get('option_c'),
            'option_d': request.form.get('option_d'),
            'correct_answer': request.form.get('correct_answer'),
            'explanation': request.form.get('explanation'),
            'time_limit': request.form.get('time_limit', type=int)
        })
        flash('Question updated!', 'success')
        return redirect(url_for('admin_dashboard'))
    q = doc_to_dict(doc_ref.get())
    return render_template('edit_question.html', question=q)

@app.route('/admin/delete-question/<q_id>', methods=['POST'])
@login_required
def delete_question(q_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    db.collection('questions').document(q_id).delete()
    flash('Question deleted.', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update-classroom', methods=['POST'])
@login_required
def update_classroom():
    if current_user.role != 'admin': return redirect(url_for('index'))
    link = request.form.get('meet_link')
    is_live = 'is_live' in request.form
    db.collection('classroom').document('main').set({
        'active_meet_link': link,
        'is_live': is_live,
        'updated_at': datetime.utcnow()
    }, merge=True)
    flash('Classroom status updated.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    # Log student access as notification
    db.collection('notifications').add({
        'message': f"Student {current_user.full_name} is active",
        'type': 'access',
        'student_id': current_user.id,
        'student_name': current_user.full_name,
        'created_at': datetime.utcnow(),
        'read': False
    })
    
    questions = [doc_to_dict(q) for q in db.collection('questions').order_by('created_at', direction=firestore.Query.DESCENDING).stream()]
    answers = [doc_to_dict(a) for a in db.collection('answers').where('student_id', '==', current_user.id).stream()]
    user_answers = {a.get('question_id'): a for a in answers}
    
    attempts = [doc_to_dict(at) for at in db.collection('attempts').where('student_id', '==', current_user.id).stream()]
    user_attempts = {at.get('question_id'): at.get('start_time').timestamp() * 1000 for at in attempts if at.get('start_time')}
    
    classroom = doc_to_dict(db.collection('classroom').document('main').get())
    return render_template('student_dashboard.html', questions=questions, user_answers=user_answers, user_attempts=user_attempts, classroom=classroom)

@app.route('/start_attempt/<q_id>')
@login_required
def start_attempt(q_id):
    attempts = db.collection('attempts').where('student_id', '==', current_user.id).where('question_id', '==', q_id).limit(1).get()
    if not attempts:
        now = datetime.utcnow()
        db.collection('attempts').add({'student_id': current_user.id, 'question_id': q_id, 'start_time': now})
        return jsonify({'start_time': now.timestamp() * 1000})
    return jsonify({'start_time': attempts[0].to_dict().get('start_time').timestamp() * 1000})

@app.route('/submit_answer', methods=['POST'])
@login_required
def submit_answer():
    q_id = request.form.get('question_id')
    ans = request.form.get('selected_option')
    q_doc = db.collection('questions').document(q_id).get()
    if not q_doc.exists: return jsonify({'status': 'error'})
    q = q_doc.to_dict()
    is_correct = ans == q.get('correct_answer')
    
    db.collection('answers').add({
        'student_id': current_user.id,
        'student_name': current_user.full_name,
        'question_id': q_id,
        'selected_option': ans,
        'is_correct': is_correct,
        'submitted_at': datetime.utcnow()
    })
    
    db.collection('notifications').add({
        'message': f"New answer from {current_user.full_name}",
        'type': 'submission',
        'student_id': current_user.id,
        'student_name': current_user.full_name,
        'question_id': q_id,
        'is_correct': is_correct,
        'created_at': datetime.utcnow(),
        'read': False
    })
    return jsonify({'status': 'success', 'is_correct': is_correct})

@app.route('/admin/get-notifications')
@login_required
def get_notifications():
    if current_user.role != 'admin': return jsonify([])
    notifs = [doc_to_dict(n) for n in db.collection('notifications').where('read', '==', False).order_by('created_at', direction=firestore.Query.DESCENDING).limit(20).stream()]
    return jsonify(notifs)

@app.route('/admin/mark-notifications-read', methods=['POST'])
@login_required
def mark_notifications_read():
    if current_user.role != 'admin': return jsonify({'status': 'ok'})
    batch = db.batch()
    notifs = db.collection('notifications').where('read', '==', False).stream()
    for n in notifs:
        batch.update(n.reference, {'read': True})
    batch.commit()
    return jsonify({'status': 'ok'})

@app.route('/init-admin')
def init_admin():
    # Set up initial admin and classroom
    admin_exists = db.collection('users').where('role', '==', 'admin').limit(1).get()
    if not admin_exists:
        db.collection('users').add({
            'username': 'admin',
            'full_name': 'Administrator',
            'password': generate_password_hash('admin123'),
            'role': 'admin',
            'created_at': datetime.utcnow()
        })
    db.collection('classroom').document('main').set({
        'active_meet_link': 'https://meet.google.com/',
        'is_live': False,
        'updated_at': datetime.utcnow()
    }, merge=True)
    return "Admin initialized: admin / admin123"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
