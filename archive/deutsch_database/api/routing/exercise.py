from fastapi import APIRouter
from db.db_orm import Exercise


router = APIRouter(prefix="/exercise")

@router.get("/all",tags=["Exercises CRUD"])
async def get_lessons():
    return {"lessons": []}

@router.delete("/all",tags=["Exercises CRUD"])
async def get_lessons():
    return {"lessons": []}

@router.post("/", tags=["Exercise CRUD"])
async def create_lesson(exercise_data: Exercise,
    db_manager: ExerciseDBManager = Depends(get_exercise_db_manager)):
    return {"lesson": {}}

@router.put("/{exercise_id}", tags=["Exercise_id CRUD"])
async def update_lesson(exercise_id: int):
    return {"lesson": {}}

@router.delete("/{exercise_id}", tags=["Exercise_id CRUD"])
async def delete_lesson(exercise_id: int):
    return {"lesson": {}}

@router.get("/{exercise_id}", tags=["Exercise_id CRUD"])
async def get_lesson(exercise_id: int):
    return {"lesson": {}}

 