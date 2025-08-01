from db.db_mngr_base import BaseDBManager
from db.db_orm import Lesson, Exercise

class DatabaseLessonManager(BaseDBManager):
    def insert(self, lesson_data):
        print(f"Inserting lesson with ID: {lesson_data['lesson_id']}")
        new_lesson = Lesson(**lesson_data)
        self.db.session.add(new_lesson)
        
        # Insert related exercises
        for exercise_data in lesson_data["content"]:
            new_exercise = Exercise(**exercise_data, lesson_id=new_lesson.lesson_id)
            self.db.session.add(new_exercise)
        
        self.db.session.commit()

    def find(self, query):
        print(f"Finding lesson with query: {query}")
        lesson = self.db.session.query(Lesson).filter_by(**query).first()
        if lesson:
            lesson.content = self.db.session.query(Exercise).filter_by(lesson_id=lesson.lesson_id).all()
        return lesson

    def update(self, lesson_id, update_data):
        print(f"Updating lesson with ID: {lesson_id}")
        lesson = self.db.session.query(Lesson).filter_by(lesson_id=lesson_id).first()
        if lesson:
            for key, value in update_data.items():
                setattr(lesson, key, value)
            self.db.session.commit()

        # Update exercises
        for exercise_data in update_data.get("content", []):
            exercise = self.db.session.query(Exercise).filter_by(block_lesson_ex_id=exercise_data['block_lesson_ex_id']).first()
            if exercise:
                for key, value in exercise_data.items():
                    setattr(exercise, key, value)
                self.db.session.commit()

    def delete(self, lesson_id):
        print(f"Deleting lesson with ID: {lesson_id}")
        exercises = self.db.session.query(Exercise).filter_by(lesson_id=lesson_id).all()
        for exercise in exercises:
            self.db.session.delete(exercise)
        lesson = self.db.session.query(Lesson).filter_by(lesson_id=lesson_id).first()
        if lesson:
            self.db.session.delete(lesson)
            self.db.session.commit()


