from fastapi import APIRouter

router = APIRouter(prefix="/topic_memory")

@router.get("/all",tags=["Topic_memories CRUD"])
async def get_lessons():
    return {"lessons": []}

@router.delete("/all",tags=["Topic_memories CRUD"])
async def get_lessons():
    return {"lessons": []}

@router.post("/", tags=["Topic_memory CRUD"])
async def create_lesson():
    return {"lesson": {}}

@router.put("/{lesson_id}", tags=["Topic_memory CRUD"])
async def update_lesson(lesson_id: int):
    return {"lesson": {}}

@router.delete("/{lesson_id}", tags=["Topic_memory CRUD"])
async def delete_lesson(lesson_id: int):
    return {"lesson": {}}

@router.get("/{lesson_id}", tags=["Topic_memory CRUD"])
async def get_lesson(lesson_id: int):
    return {"lesson": {}}
