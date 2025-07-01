from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Replace with your actual password and database name
DATABASE_URL = "postgresql://postgres:broWTH#666@localhost:5432/notesdb"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ Define Base here (DO NOT import from anywhere else)
Base = declarative_base()

