from app import app
from models import get_engine, Base, Category, get_session
from sqlalchemy import text

# Default categories to seed
DEFAULT_CATEGORIES = [
    {"name": "General Notes", "description": "General notes and thoughts"},
    {"name": "Content Ideas", "description": "Ideas for blog, YouTube, social media content"},
    {"name": "VibeCoding Projects", "description": "Coding and development projects"},
    {"name": "Stock Trading", "description": "Stock market notes and analysis"},
    {"name": "To-Do", "description": "Tasks and action items"},
    {
        "name": "To Learn",
        "description": "Learning resources and educational content",
        "subcategories": [
            {"name": "Reading List", "description": "Articles, books, and reading material to learn from"},
            {"name": "Videos", "description": "Video tutorials, courses, and educational videos"},
        ]
    },
]

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
            
            # Seed default categories if they don't exist
            session = get_session()
            try:
                for cat_data in DEFAULT_CATEGORIES:
                    existing = session.query(Category).filter(Category.name == cat_data["name"]).first()
                    if not existing:
                        category = Category(
                            name=cat_data["name"],
                            description=cat_data["description"]
                        )
                        session.add(category)
                        session.flush()  # Flush to get the category ID for subcategories
                        print(f"✅ Created category: {cat_data['name']}")
                    else:
                        category = existing
                        print(f"⏭️ Category already exists: {cat_data['name']}")
                    
                    # Seed subcategories if defined
                    for sub_data in cat_data.get("subcategories", []):
                        existing_sub = session.query(Category).filter(
                            Category.name == sub_data["name"],
                            Category.parent_id == category.id
                        ).first()
                        if not existing_sub:
                            subcategory = Category(
                                name=sub_data["name"],
                                description=sub_data["description"],
                                parent_id=category.id
                            )
                            session.add(subcategory)
                            print(f"  ✅ Created subcategory: {sub_data['name']} (under {cat_data['name']})")
                        else:
                            print(f"  ⏭️ Subcategory already exists: {sub_data['name']}")
                
                session.commit()
            finally:
                session.close()
                
        except Exception as e:
            print(f"❌ Error initializing tables: {e}")

if __name__ == "__main__":
    init_tables()

