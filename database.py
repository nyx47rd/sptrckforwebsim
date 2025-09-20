import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# This is the base class for our models
Base = declarative_base()

# Database URL is taken from the environment variable 'DATABASE_URL'
# This is for connecting to a production database like PostgreSQL on Vercel.
DATABASE_URL = os.getenv("DATABASE_URL")

# If DATABASE_URL is not set, we fall back to a local SQLite database.
# This is useful for local development and testing.
if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
else:
    print("DATABASE_URL not found, falling back to SQLite for local development.")
    SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
    # `connect_args` is needed only for SQLite to allow multi-threaded access.
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Dependency to get a DB session for each request.
    It ensures the database session is always closed after the request.
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
    # Import all models here before calling create_all
    # to ensure they are registered with the Base metadata
    import models
    Base.metadata.create_all(bind=engine)
