from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Lesson(Base):
    __tablename__ = 'lessons'
    
    lesson_id = Column(String(255), primary_key=True)
    block = Column(String(255))
    content = relationship('Exercise', back_populates='lesson')
    started_at = Column(DateTime)
    last_time = Column(DateTime)
    completed_percent = Column(Float)


class Exercise(Base):
    __tablename__ = 'exercises'

    block_lesson_ex_id = Column(String(255), primary_key=True)
    type = Column(String(255))
    started_at = Column(DateTime)
    last_time = Column(DateTime)
    completion_speed = Column(Float)
    vocaboulary_pointer = Column(String(255))
    lesson_id = Column(String(255), ForeignKey('lessons.lesson_id'))
    lesson = relationship("Lesson", back_populates="content")
    completed = Column(Boolean)


class TopicMemory(Base):
    __tablename__ = 'topic_memory'

    topic = Column(String(255), primary_key=True)
    skill_type = Column(String(255))
    lesson_content_id = Column(String(255))
    ease_factor = Column(Float)
    interval = Column(Integer)
    next_repeat = Column(DateTime)
    repetition = Column(Integer)
    last_review = Column(DateTime) 


class FeedbackLog (Base):
    __tablename__ = 'feedback_log'

    id = Column(Integer, primary_key=True)
    student_id = Column(String(255))
    exercise_id = Column(String(255))
    topic = Column(String(255))
    skill_type = Column(String(255))
    score = Column(Integer)
    timestamp = Column(DateTime)
    lesson_content_id = Column(String(255))
    feedback_type = Column(String(255))


