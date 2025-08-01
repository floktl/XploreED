from db.db_connection import init_connection, create_db
from dotenv import load_dotenv
from db.db_mngr_lesson import DatabaseLessonManager 
import os
from db.db_orm import Base
from api.app import app

def main ():
    app()
    load_dotenv()
    create_db()
    engine = init_connection()
    Base.metadata.create_all(engine)
    # db_lesson_manager()

if __name__ == "__main__" :
    main()