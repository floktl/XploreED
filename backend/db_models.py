from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    Boolean,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship
import datetime
import os

Base = declarative_base()

# ----- Core entities -----
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    password = Column(String)
    status = Column(String)
    level = Column(String)
    improvement_time = Column(String)


class LessonContent(Base):
    __tablename__ = "lesson_content"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_id = Column(Integer)
    title = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    target_user = Column(String)
    published = Column(Boolean, default=False)
    num_blocks = Column(Integer, default=0)
    ai_enabled = Column(Boolean, default=False)

    blocks = relationship("LessonBlock", back_populates="lesson")


class LessonBlock(Base):
    __tablename__ = "lesson_blocks"

    lesson_id = Column(Integer, ForeignKey("lesson_content.lesson_id"), primary_key=True)
    block_id = Column(String, primary_key=True)

    lesson = relationship("LessonContent", back_populates="blocks")


class LessonProgress(Base):
    __tablename__ = "lesson_progress"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("students.id"))
    lesson_id = Column(Integer, ForeignKey("lesson_content.lesson_id"))
    block_id = Column(String)
    completed = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True)
    block_lesson_id = Column(String)
    content = Column(Text)
    last_time = Column(DateTime)
    started_at = Column(DateTime)
    completion_speed = Column(Float)


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True)
    block_lesson_ex_id = Column(String)
    type = Column(String)
    last_time = Column(DateTime)
    started_at = Column(DateTime)
    completion_speed = Column(Float)
    feedback_id = Column(Integer, ForeignKey("feedback.id"))

    feedback = relationship("Feedback", back_populates="exercise")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)
    grammar_grade = Column(Integer)
    structure_grade = Column(Integer)
    n_grade = Column(Integer)
    speed = Column(Integer)
    creativity = Column(Integer)
    spelling = Column(Integer)

    exercise = relationship("Exercise", uselist=False, back_populates="feedback")


# ----- Vocabulary and spaced repetition -----
class Vocab(Base):
    __tablename__ = "vocab"

    id = Column(Integer, primary_key=True)
    type = Column(String)
    word = Column(String)
    translation = Column(String)
    sm2_interval = Column(Integer)
    sm2_due_date = Column(DateTime)
    sm2_ease = Column(Float)
    repetitions = Column(Integer)
    sm2_last_review = Column(DateTime)
    quality = Column(Float)
    completed_percent = Column(Float)
    completed = Column(Boolean)


class TopicMemory(Base):
    __tablename__ = "topic_memory"

    id = Column(Integer, primary_key=True)
    topic = Column(String)
    skill_type = Column(String)
    lesson_content_id = Column(Integer)
    ease_factor = Column(Float)
    intervall = Column(Integer)
    next_repeat = Column(DateTime)
    repetitions = Column(Integer)
    last_review = Column(DateTime)


# ----- Feedback tracking -----
class FeedbackLog(Base):
    __tablename__ = "feedback_log"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    exercise_id = Column(Integer, ForeignKey("exercises.id"))
    topic = Column(String)
    skill_type = Column(String)
    score = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    lesson_block_id = Column(Integer)
    feedback_type = Column(String)
    theory = Column(Text)
    fluency = Column(Text)


class FluencyTracker(Base):
    __tablename__ = "fluency_tracker"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    topic = Column(String)
    skill_type = Column(String)
    rolling_avg_score = Column(Float)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)
    improvement_sugg = Column(Text)
    creativity = Column(Float)
    speed = Column(Float)
    spelling = Column(Float)


# ----- Other tables derived from the existing project -----
class Result(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True)
    username = Column(String)
    level = Column(Integer)
    correct = Column(Integer)
    answer = Column(Text)
    timestamp = Column(DateTime)


class VocabLog(Base):
    __tablename__ = "vocab_log"

    id = Column(Integer, primary_key=True)
    username = Column(String)
    vocab = Column(String)
    translation = Column(String)
    repetitions = Column(Integer, default=0)
    interval_days = Column(Integer, default=1)
    ef = Column(Float, default=2.5)
    next_review = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    context = Column(Text)
    exercise = Column(Text)


class SupportFeedback(Base):
    __tablename__ = "support_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


DB_PATH = os.getenv("DB_FILE", "mock.db")
engine = create_engine(f"sqlite:///{DB_PATH}")


def create_tables():
    Base.metadata.create_all(engine)


