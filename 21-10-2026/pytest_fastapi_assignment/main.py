from fastapi import FastAPI
from pydantic import BaseModel

class Task(BaseModel):
    id: int
    title: str
    status: str

tasks = [
    {
        "id": 1,
        "title": "Prepare report",
        "status": "Pending"
    },
    {
        "id": 2,
        "title": "Review invoice",
        "status": "Completed"
    },
    {
        "id": 3,
        "title": "Update dashboard",
        "status": "Pending"
    }
]

app = FastAPI()

@app.get("/tasks")
def read_tasks():
    return tasks

@app.get("/tasks/{task_id}")
def read_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return {
                "message": f"Task {task_id} was found",
                "task": task
            }

    return {"message": "Task not found"}

@app.post("/tasks")
def create_task(task: Task):
    tasks.append(task.model_dump())

    return {
        "message": f"Task {task.title} was created",
    }

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: Task):
    for t in tasks:
        if t["id"] == task_id:
            t["title"] = task.title
            t["status"] = task.status
            return {
                "message": f"Task {task_id} was updated",
            }

    return {
        "message": "Task not found"
    }

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    for t in tasks:
        if t["id"] == task_id:
            tasks.remove(t)
            return {
                "message": f"Task {task_id} was deleted",
            }

    return {
        "message": "Task not found"
    }