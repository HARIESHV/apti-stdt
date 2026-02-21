from app import app, init_db
import sys

if __name__ == "__main__":
    print("🚀 Initializing database...")
    try:
        init_db()
        print("✅ Database initialization complete!")
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        sys.exit(1)
