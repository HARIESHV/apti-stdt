from app import app, db, User, Classroom
from werkzeug.security import generate_password_hash
from datetime import datetime

def init_db():
    with app.app_context():
        print("🚀 Initializing database (SQL)...")
        db.create_all()
        
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
            print("✅ Default admin created: admin / admin123")
        
        print("✅ Database initialization complete!")

if __name__ == '__main__':
    init_db()
