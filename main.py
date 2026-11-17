from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str | None = None


class Task(BaseModel):
    id: int
    title: str
    description: str | None = None
    completed: bool = False


tasks: list[Task] = []
next_id = 1


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/tasks", response_model=Task, status_code=201)
def create_task(payload: TaskCreate):
    global next_id
    task = Task(id=next_id, title=payload.title, description=payload.description)
    tasks.append(task)
    next_id += 1
    return task


@app.get("/tasks", response_model=list[Task])
def list_tasks():
    return tasks


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    for task in tasks:
        if task.id == task_id:
            return task
    raise HTTPException(status_code=404, detail="Task not found")