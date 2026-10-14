import pandas as pd
from sqlalchemy import (create_engine, MetaData, Table, Column, Integer, String,
                        Text, Float, Date, DateTime, Boolean, text)
import config

engine = create_engine(config.DATABASE_URL, pool_pre_ping=True)
metadata = MetaData()

users = Table("users", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(100), nullable=False),
    Column("email", String(120), unique=True, nullable=False),
    Column("password_hash", String(255), nullable=False),
    Column("role", String(20), nullable=False),      # student ya teacher
    Column("roll_no", String(30)),
)

results = Table("results", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("roll_no", String(30), nullable=False),
    Column("student_name", String(100), nullable=False),
    Column("subject_code", String(20), nullable=False),
    Column("subject_name", String(120), nullable=False),
    Column("marks", Float, nullable=False),
    Column("max_marks", Float, nullable=False),
    Column("status", String(10)),                    # pass / fail
)

timetable = Table("timetable", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("day", String(15), nullable=False),
    Column("start_time", String(5), nullable=False),  # 24 hr, jaise 13:20
    Column("end_time", String(5), nullable=False),
    Column("subject_code", String(20), nullable=False),
    Column("subject_name", String(120), nullable=False),
    Column("teacher", String(100)),
    Column("kind", String(10)),                       # Lecture / Lab
    Column("room", String(100)),
)

current_topics = Table("current_topics", metadata,
    Column("subject_code", String(20), primary_key=True),
    Column("unit", String(10)),
    Column("topic", String(255)),
    Column("updated_on", DateTime),
)

assignments = Table("assignments", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("subject_code", String(20), nullable=False),
    Column("subject_name", String(120)),
    Column("title", String(150), nullable=False),
    Column("description", Text),
    Column("posted_by", String(100)),
    Column("posted_on", DateTime),
    Column("due_date", Date),
    Column("max_marks", Integer),
    Column("file_name", String(255)),
)

notifications = Table("notifications", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, nullable=False),
    Column("message", String(255), nullable=False),
    Column("created_on", DateTime),
    Column("is_read", Boolean, default=False),
    Column("note_key", String(120)),                  # duplicate reminder rokne ke liye
)


def init_db():
    metadata.create_all(engine)


def query_df(sql, params=None):
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})
