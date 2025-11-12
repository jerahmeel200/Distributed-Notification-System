"""
Database configuration and session management
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
import os
import time
import sys
from models import Base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user_service:userpass123@localhost:5432/user_db"
)

# Validate connection string has database name
if DATABASE_URL and "/" in DATABASE_URL:
    # Ensure database name is present (after last /)
    parts = DATABASE_URL.rsplit("/", 1)
    if len(parts) == 2 and not parts[1] or parts[1].split("?")[0] == "":
        raise ValueError("Database name is missing from DATABASE_URL. Expected format: postgresql://user:pass@host:port/dbname")
    print(f"Connecting to database: {parts[1].split('?')[0] if len(parts) == 2 else 'unknown'}")
else:
    raise ValueError("Invalid DATABASE_URL format")

# Add retry logic for database connection
engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True,
    connect_args={"connect_timeout": 10}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables with retry logic"""
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            # Test connection first
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # Create tables
            Base.metadata.create_all(bind=engine)
            print("Database initialized successfully")
            return
        except OperationalError as e:
            if attempt < max_retries - 1:
                print(f"Database connection failed (attempt {attempt + 1}/{max_retries}): {e}")
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Failed to initialize database after {max_retries} attempts: {e}")
                raise
        except Exception as e:
            print(f"Error initializing database: {e}")
            raise

