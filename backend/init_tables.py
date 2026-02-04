from app import app
from models import get_engine, Base
from sqlalchemy import text

def init_tables():
    print("Initializing database tables...")
    with app.app_context():
        try:
            # Create all tables defined in models.py (includes UsageLogs)
            engine = get_engine()
            Base.metadata.create_all(bind=engine)
            print("✅ Tables verified/created successfully.")
            
            # Double check usage_logs exists
            with engine.connect() as conn:
                result = conn.execute(text("SELECT to_regclass('public.usage_logs')"))
                if result.scalar():
                    print("✅ 'usage_logs' table confirmed.")
                else:
                    print("❌ 'usage_logs' table MISSING despite create_all.")
        except Exception as e:
            print(f"❌ Error initializing tables: {e}")

if __name__ == "__main__":
    init_tables()
