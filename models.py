from sqlalchemy import Column, Integer, String
from database import Base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(String)
    user_email = Column(String, ForeignKey("users.email"))  # <-- Link to user

    # Optional: for reverse relation
    user = relationship("User", back_populates="notes")
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    notes = relationship("Note", back_populates="user")