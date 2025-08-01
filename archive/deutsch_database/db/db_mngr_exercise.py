from db.db_mngr_base import BaseDBManager
from sqlalchemy.orm import Session
from fastapi import Depends
from db.db_orm import Exercise

def get_exercise_db_manager(db: Session = Depends(get_db)):
    return DBExerciseManager(db)

class DBExerciseManager(BaseDBManager):
    def insert(self, exercise_data):
        # print(f"Inserting lesson with ID: {lesson_data['lesson_id']}")
        new_exercise = Exercise(**exercise_data)
        self.db.add(new_exercise)
        self.db.commit()