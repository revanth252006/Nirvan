from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# We'll use SQLite for Phase 1 to get up and running instantly without needing you to install PostgreSQL yet.
# We will migrate to PostgreSQL in Phase 2 or 3.
SQLALCHEMY_DATABASE_URL = "sqlite:///./nirvan_v2.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
