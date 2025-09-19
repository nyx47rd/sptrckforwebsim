import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base  # Import Base from models

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Database URL is taken from the environment variable 'DATABASE_URL'
# This is for connecting to a production database like PostgreSQL on Vercel.
DATABASE_URL = os.getenv("DATABASE_URL")

# If DATABASE_URL is not set, we fall back to a local SQLite database.
# This is useful for local development and testing.
if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
else:
    print("DATABASE_URL not found, falling back to SQLite.")
    SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
    # `connect_args` is needed only for SQLite to allow multi-threaded access.
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Dependency to get a DB session for each request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_db_and_tables():
    """
    Creates all database tables based on the models.
    This should be called on application startup.
    """
    Base.metadata.create_all(bind=engine)
