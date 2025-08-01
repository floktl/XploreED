from fastapi import APIRouter

router = APIRouter(prefix="/feedback")

@router.get("/all",tags=["Feedbacks CRUD"])
async def get_lessons():
    return {"lessons": []}

@router.delete("/all",tags=["Feedbacks CRUD"])
async def get_lessons():
    return {"lessons": []}

@router.post("/", tags=["Feedback CRUD"])
async def create_lesson():
    return {"lesson": {}}

@router.put("/{lesson_id}", tags=["Feedback CRUD"])
async def update_lesson(lesson_id: int):
    return {"lesson": {}}

@router.delete("/{lesson_id}", tags=["Feedback CRUD"])
async def delete_lesson(lesson_id: int):
    return {"lesson": {}}

@router.get("/{lesson_id}", tags=["Feedback CRUD"])
async def get_lesson(lesson_id: int):
    return {"lesson": {}}
