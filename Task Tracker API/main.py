from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, constr, validator
from datetime import date
from typing import Optional, List

app = FastAPI()

# In-memory mock databases
user_db = {}
task_db = {}

next_user_id = 1
next_task_id = 1

# -------------------------------
# 📌 Models
# -------------------------------

class UserCreate(BaseModel):
    username: constr(min_length=3, max_length=20)
    email: EmailStr

class UserInfo(BaseModel):
    id: int
    username: str
    email: EmailStr

class TaskInput(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: date
    user_id: int

    @validator("due_date")
    def future_due_date(cls, value):
        if value < date.today():
            raise ValueError("Due date can't be in the past.")
        return value

class TaskDetails(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    due_date: date
    status: str
    user_id: int

    @validator("due_date")
    def check_due_date(cls, value):
        if value < date.today():
            raise ValueError("Due date must be today or later.")
        return value

class TaskStatusUpdate(BaseModel):
    status: str

    @validator("status")
    def validate_status(cls, val):
        valid_statuses = ["pending", "in_progress", "completed"]
        if val not in valid_statuses:
            raise ValueError(f"Invalid status. Choose from: {', '.join(valid_statuses)}")
        return val

# -------------------------------
# 👤 User Routes
# -------------------------------

@app.post("/users/", response_model=UserInfo)
def register_user(payload: UserCreate):
    global next_user_id
    user_info = payload.dict()
    user_info["id"] = next_user_id
    user_db[next_user_id] = user_info
    next_user_id += 1
    return user_info

@app.get("/users/{user_id}", response_model=UserInfo)
def fetch_user(user_id: int):
    if user_id not in user_db:
        raise HTTPException(status_code=404, detail="User does not exist")
    return user_db[user_id]

# -------------------------------
# ✅ Task Routes
# -------------------------------

@app.post("/tasks/", response_model=TaskDetails)
def add_task(payload: TaskInput):
    global next_task_id
    if payload.user_id not in user_db:
        raise HTTPException(status_code=404, detail="No user with this ID")
    
    task_info = payload.dict()
    task_info["id"] = next_task_id
    task_info["status"] = "pending"
    task_db[next_task_id] = task_info
    next_task_id += 1
    return task_info

@app.get("/tasks/{task_id}", response_model=TaskDetails)
def fetch_task(task_id: int):
    if task_id not in task_db:
        raise HTTPException(status_code=404, detail="Task not found")
    return task_db[task_id]

@app.put("/tasks/{task_id}", response_model=TaskDetails)
def update_task(task_id: int, payload: TaskStatusUpdate):
    if task_id not in task_db:
        raise HTTPException(status_code=404, detail="Task not found")
    task_db[task_id]["status"] = payload.status
    return task_db[task_id]

@app.get("/users/{user_id}/tasks", response_model=List[TaskDetails])
def get_tasks_for_user(user_id: int):
    if user_id not in user_db:
        raise HTTPException(status_code=404, detail="User not found")
    return [task for task in task_db.values() if task["user_id"] == user_id]
