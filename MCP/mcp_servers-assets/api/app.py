from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import uuid4
import sqlite3
import uvicorn
from contextlib import contextmanager


app = FastAPI()

# Database file path
DB_PATH = "tasks.db"


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: Optional[str] = None
    completed: bool = False
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize the database and create the tasks table if it doesn't exist"""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                completed INTEGER NOT NULL DEFAULT 0,
                due_date TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()


@app.get("/tasks")
def get_tasks():
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM tasks")
        rows = cursor.fetchall()
        tasks = []
        for row in rows:
            task_dict = dict(row)
            # Convert string dates back to datetime objects
            if task_dict["due_date"]:
                task_dict["due_date"] = datetime.fromisoformat(task_dict["due_date"])
            task_dict["created_at"] = datetime.fromisoformat(task_dict["created_at"])
            task_dict["updated_at"] = datetime.fromisoformat(task_dict["updated_at"])
            task_dict["completed"] = bool(task_dict["completed"])
            tasks.append(Task(**task_dict))
        return tasks


@app.post("/tasks")
def create_task(task: Task):
    with get_db() as conn:
        # Convert datetime objects to ISO format strings for storage
        task_dict = task.model_dump()
        task_dict["due_date"] = task_dict["due_date"].isoformat() if task_dict["due_date"] else None
        task_dict["created_at"] = task_dict["created_at"].isoformat()
        task_dict["updated_at"] = task_dict["updated_at"].isoformat()
        task_dict["completed"] = 1 if task_dict["completed"] else 0
        
        conn.execute("""
            INSERT INTO tasks (id, title, description, completed, due_date, created_at, updated_at)
            VALUES (:id, :title, :description, :completed, :due_date, :created_at, :updated_at)
        """, task_dict)
        
        return task


@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        
        if row is None:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task_dict = dict(row)
        # Convert string dates back to datetime objects
        if task_dict["due_date"]:
            task_dict["due_date"] = datetime.fromisoformat(task_dict["due_date"])
        task_dict["created_at"] = datetime.fromisoformat(task_dict["created_at"])
        task_dict["updated_at"] = datetime.fromisoformat(task_dict["updated_at"])
        task_dict["completed"] = bool(task_dict["completed"])
        
        return Task(**task_dict)


@app.put("/tasks/{task_id}")
def update_task(task_id: str, updated_task: Task):
    with get_db() as conn:
        # First, check if task exists and get its created_at
        cursor = conn.execute("SELECT created_at FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        
        if row is None:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Prepare update data
        task_dict = updated_task.model_dump()
        task_dict["id"] = task_id
        task_dict["created_at"] = row["created_at"]  # Preserve original created_at
        task_dict["updated_at"] = datetime.now().isoformat()
        task_dict["due_date"] = task_dict["due_date"].isoformat() if task_dict["due_date"] else None
        task_dict["completed"] = 1 if task_dict["completed"] else 0
        
        conn.execute("""
            UPDATE tasks 
            SET title = :title, description = :description, completed = :completed,
                due_date = :due_date, updated_at = :updated_at
            WHERE id = :id
        """, task_dict)
        
        # Fetch and return updated task
        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        task_dict = dict(row)
        if task_dict["due_date"]:
            task_dict["due_date"] = datetime.fromisoformat(task_dict["due_date"])
        task_dict["created_at"] = datetime.fromisoformat(task_dict["created_at"])
        task_dict["updated_at"] = datetime.fromisoformat(task_dict["updated_at"])
        task_dict["completed"] = bool(task_dict["completed"])
        
        return Task(**task_dict)


@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {"message": "Task deleted"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
