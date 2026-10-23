import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

# Default to the user's specified connection string, with optional env override
raw_url = os.getenv("SQLALCHEMY_DATABASE_URL", "mysql+pymysql://root:Ramc%40123@localhost/hotel_resort")
SQLALCHEMY_DATABASE_URL = raw_url.rstrip("/")

# Engine configuration with connection pooling and auto-reconnect
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=10,
        max_overflow=20
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
