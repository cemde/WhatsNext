from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import db

SQLALCHEMY_DATABASE_URL = f"postgresql://{db.user}:{db.password}@{db.hostname}:{db.port}/{db.database}"

# Configure connection pool for production use
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=5,  # Number of connections to keep in the pool
    max_overflow=10,  # Max additional connections beyond pool_size
    pool_pre_ping=True,  # Verify connections are alive before using
    pool_recycle=3600,  # Recycle connections after 1 hour to prevent stale connections
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
