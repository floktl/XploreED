from fastapi import APIRouter

router = APIRouter(prefix="/lesson")

@router.get("/all",tags=["Lessons CRUD"])
async def get_lessons():
    return {"lessons": []}

@router.delete("/all",tags=["Lessons CRUD"])
async def get_lessons():
    return {"lessons": []}

@router.post("/", tags=["Lesson_id CRUD"])
async def create_lesson():
    return {"lesson": {}}

@router.put("/{lesson_id}", tags=["Lesson_id CRUD"])
async def update_lesson(lesson_id: int):
    return {"lesson": {}}

@router.delete("/{lesson_id}", tags=["Lesson_id CRUD"])
async def delete_lesson(lesson_id: int):
    return {"lesson": {}}

@router.get("/{lesson_id}", tags=["Lesson_id CRUD"])
async def get_lesson(lesson_id: int):
    return {"lesson": {}}

 
