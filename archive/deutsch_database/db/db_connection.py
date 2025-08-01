from sqlalchemy import create_engine
import os
import pymysql
from const import (DB_HOST,
                   DB_NAME,
                   DB_PASSWORD,
                   DB_USER,
                   DB_PORT
)

def create_db():
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        port=3306
    )

    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cursor.close()
    conn.close()

def init_connection():
    engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    return engine