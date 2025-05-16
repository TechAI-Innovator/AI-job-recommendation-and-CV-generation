# db.py
from sqlalchemy import (Column, Integer,
                        String, Text,
                        ForeignKey, DateTime,
                        Boolean, JSON)
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from db import Base
from datetime import datetime

class User(Base, UserMixin):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(200), nullable=False)
    
    surname = Column(String(100))
    middle_name = Column(String(100))
    first_name = Column(String(100))
    phone = Column(String(20))
    preferred_titles = Column(String(100))
    location = Column(String(100))
    min_salary = Column(String(50))
    education = Column(JSON)
    skills = Column(Text)
    experience = Column(JSON)
    github = Column(String(150))
    linkedin = Column(String(150))
    summary = Column(Text)
    preferred_locations = Column(String(100))
    employment_type  = Column(String(100)) 
    experience_level = Column(String(50))
    preferred_industries = Column(String(150))
    job_keywords = Column(String(150))
    
    # Relationships
    cvs = relationship("CV", back_populates="user")
    feedback = relationship("Feedback", back_populates="user")
    job_recommendations = relationship("JobRecommendation", back_populates="user")

class JobRecommendation(Base):
    __tablename__ = "job_recommendations"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_title = Column(String(150))
    company = Column(String(150))
    salary = Column(String(100))
    location = Column(String(100))
    description = Column(Text)
    url = Column(String(300))
    match_score = Column(Integer)  # Optional match score (0–100)
    timestamp = Column(DateTime, default=datetime.now())

    user = relationship("User", back_populates="job_recommendations")

class CV(Base):
    __tablename__ = "cvs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)  # Raw text or HTML
    file_path = Column(String(300)) 
    generated_on = Column(DateTime, default=datetime.now())

    user = relationship("User", back_populates="cvs")

class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.now())

    user = relationship("User", back_populates="feedback")
