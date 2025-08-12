import os
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "mvnestdb")
DB_USERNAME = os.getenv("DB_USERNAME", "postgresql")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")

DATABASE_URL = f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# The engine is exported to be used by the lifespan function in config.py
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()  # commit only if no errors
    except:
        db.rollback()  # rollback on any exception
        raise
    finally:
        db.close()