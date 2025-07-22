#!/usr/bin/env python3
"""
Database initialization script for SignAware AI.
This script creates the necessary database tables.
"""

import sys
import os

# Add the app directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from app.database import Base
from app.models import User, Document, ChatMessage
from app.config import get_settings

def init_db():
    """Initialize the database with all tables."""
    settings = get_settings()
    
    print(f"Connecting to database: {settings.database_url}")
    
    # Create engine
    engine = create_engine(settings.database_url)
    
    try:
        # Test connection first
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if result.fetchone():
                print("✅ Database connection test successful!")
        
        # Create uuid-ossp extension if it doesn't exist
        print("Creating UUID extension...")
        with engine.connect() as conn:
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
            conn.commit()
            print("✅ UUID extension created/verified!")
        
        # Create all tables
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        # Verify tables exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        expected_tables = ['users', 'documents', 'chat_messages']
        for table in expected_tables:
            if table in tables:
                print(f"✅ Table '{table}' created successfully")
            else:
                print(f"⚠️  Table '{table}' not found")
        
        print(f"\n📊 Database Summary:")
        print(f"   - Total tables created: {len(tables)}")
        print(f"   - Tables: {', '.join(tables)}")
                
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check your DATABASE_URL in the .env file")
        print("3. Ensure the database exists and is accessible")
        print("4. Verify PostgreSQL user has proper permissions")
        sys.exit(1)

def create_sample_data():
    """Create some sample data for testing (optional)."""
    settings = get_settings()
    engine = create_engine(settings.database_url)
    
    from sqlalchemy.orm import sessionmaker
    from app.models import User, DocumentType, DocumentStatus
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if we already have users
        user_count = db.query(User).count()
        if user_count > 0:
            print(f"✅ Database already has {user_count} users. Skipping sample data creation.")
            return
        
        # Create a sample user
        sample_user = User(
            email="admin@signaware.ai",
            firstName="Admin",
            lastName="User",
            role="admin",
            isEmailVerified=True,
            isActive=True
        )
        
        db.add(sample_user)
        db.commit()
        db.refresh(sample_user)
        
        print(f"✅ Sample user created: {sample_user.email} (ID: {sample_user.id})")
        
        # Create a sample document
        from app.models import Document
        sample_document = Document(
            title="Sample Terms of Service",
            content="This is a sample terms of service document for testing purposes.",
            type=DocumentType.TERMS_OF_SERVICE,
            status=DocumentStatus.PENDING,
            userId=sample_user.id
        )
        
        db.add(sample_document)
        db.commit()
        db.refresh(sample_document)
        
        print(f"✅ Sample document created: {sample_document.title} (ID: {sample_document.id})")
        
    except Exception as e:
        print(f"⚠️  Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 SignAware AI Database Initialization")
    print("=" * 50)
    
    # Initialize database
    init_db()
    
    # Ask user if they want to create sample data
    create_sample = input("\n❓ Create sample data for testing? (y/N): ").lower().strip()
    if create_sample in ['y', 'yes']:
        print("\n📝 Creating sample data...")
        create_sample_data()
    
    print("\n✨ Database initialization completed!")
    print("\n📋 Next steps:")
    print("   1. Start the application: uv run python run.py")
    print("   2. Test the APIs: uv run python scripts/test_api.py")
    print("   3. Visit http://localhost:8000/docs for API documentation") 