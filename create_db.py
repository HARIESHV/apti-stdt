import pymysql

# Step 1: Create the database
try:
    conn = pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        password=''
    )
    with conn.cursor() as cur:
        cur.execute("CREATE DATABASE IF NOT EXISTS aptipro CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print("✅ Database 'aptipro' created (or already exists).")
    conn.commit()
    conn.close()
except Exception as e:
    print(f"❌ MySQL connection error: {e}")
    exit(1)

# Step 2: Create all tables via SQLAlchemy
try:
    from app import app, db
    with app.app_context():
        db.create_all()
        print("✅ All tables created successfully!")
        print("✅ Default admin user ready: admin / admin123")
except Exception as e:
    print(f"❌ Table creation error: {e}")
