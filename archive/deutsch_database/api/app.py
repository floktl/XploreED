from fastapi import FastAPI, APIRouter
from api.routing.lesson import router as lesson_router
from api.routing.exercise import router as exercise_router
from api.routing.topic_memory import router as topic_memory_router
from api.routing.feedback import router as feedback_log_router


app = FastAPI()

app.include_router(lesson_router)
app.include_router(exercise_router)
app.include_router(topic_memory_router)
app.include_router(feedback_log_router)


@app.get("/")
async def root():
    return {"message": "DB Manager"}