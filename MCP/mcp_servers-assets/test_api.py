import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import sqlite3
import os
from api.app import app

# Use a test database file
TEST_DB_PATH = "test_tasks.db"

@pytest.fixture(autouse=True)
def reset_tasks(monkeypatch):
    """Reset the database before and after each test"""
    # Patch the DB_PATH to use test database
    monkeypatch.setattr("api.app.DB_PATH", TEST_DB_PATH)
    
    # Initialize test database
    conn = sqlite3.connect(TEST_DB_PATH)
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
    conn.commit()
    conn.close()
    
    # Clear all tasks before test
    conn = sqlite3.connect(TEST_DB_PATH)
    conn.execute("DELETE FROM tasks")
    conn.commit()
    conn.close()
    
    yield
    
    # Clean up after test
    conn = sqlite3.connect(TEST_DB_PATH)
    conn.execute("DELETE FROM tasks")
    conn.commit()
    conn.close()

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    """Clean up test database file after all tests"""
    yield
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

# Create a test client
client = TestClient(app)


def test_get_tasks_empty():
    """Test getting tasks when list is empty"""
    response = client.get("/tasks")
    assert response.status_code == 200
    assert response.json() == []


def test_create_task():
    """Test creating a new task"""
    task_data = {
        "title": "Test Task",
        "description": "This is a test task",
        "completed": False
    }
    response = client.post("/tasks", json=task_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "This is a test task"
    assert data["completed"] == False
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_task_with_due_date():
    """Test creating a task with a due date"""
    due_date = "2024-12-31T23:59:59"
    task_data = {
        "title": "Task with due date",
        "due_date": due_date
    }
    response = client.post("/tasks", json=task_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Task with due date"
    assert data["due_date"] == due_date


def test_get_tasks_after_creation():
    """Test getting all tasks after creating some"""
    # Create multiple tasks
    task1 = {"title": "Task 1"}
    task2 = {"title": "Task 2"}
    
    client.post("/tasks", json=task1)
    client.post("/tasks", json=task2)
    
    response = client.get("/tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Task 1"
    assert data[1]["title"] == "Task 2"


def test_get_task_by_id():
    """Test getting a specific task by ID"""
    # Create a task
    task_data = {"title": "Find me"}
    create_response = client.post("/tasks", json=task_data)
    task_id = create_response.json()["id"]
    
    # Get the task by ID
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Find me"
    assert data["id"] == task_id


def test_get_task_not_found():
    """Test getting a task that doesn't exist"""
    response = client.get("/tasks/non-existent-id")
    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_update_task():
    """Test updating a task"""
    # Create a task
    task_data = {"title": "Original Title"}
    create_response = client.post("/tasks", json=task_data)
    task_id = create_response.json()["id"]
    
    # Update the task
    updated_data = {
        "id": task_id,
        "title": "Updated Title",
        "description": "Updated description",
        "completed": True
    }
    response = client.put(f"/tasks/{task_id}", json=updated_data)
    assert response.status_code == 200
    
    # Verify the task was updated
    get_response = client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated description"
    assert data["completed"] == True


def test_update_task_not_found():
    """Test updating a task that doesn't exist"""
    task_data = {
        "id": "non-existent-id",
        "title": "Updated Title"
    }
    response = client.put("/tasks/non-existent-id", json=task_data)
    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_delete_task():
    """Test deleting a task"""
    # Create a task
    task_data = {"title": "To be deleted"}
    create_response = client.post("/tasks", json=task_data)
    task_id = create_response.json()["id"]
    
    # Verify task exists
    get_response = client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 200
    
    # Delete the task
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json() == {"message": "Task deleted"}
    
    # Verify task is deleted
    get_response = client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 404
    assert get_response.json() == {"detail": "Task not found"}


def test_delete_task_not_found():
    """Test deleting a task that doesn't exist"""
    response = client.delete("/tasks/non-existent-id")
    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_full_crud_workflow():
    """Test a complete CRUD workflow"""
    # Create
    task_data = {"title": "Workflow Test", "description": "Testing full workflow"}
    create_response = client.post("/tasks", json=task_data)
    assert create_response.status_code == 200
    task_id = create_response.json()["id"]
    
    # Read
    get_response = client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Workflow Test"
    
    # Update
    updated_data = {
        "id": task_id,
        "title": "Updated Workflow Test",
        "completed": True
    }
    update_response = client.put(f"/tasks/{task_id}", json=updated_data)
    assert update_response.status_code == 200
    
    # Verify update
    get_response = client.get(f"/tasks/{task_id}")
    assert get_response.json()["title"] == "Updated Workflow Test"
    
    # Delete
    delete_response = client.delete(f"/tasks/{task_id}")
    assert delete_response.status_code == 200
    
    # Verify deletion
    get_response = client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 404
    assert get_response.json() == {"detail": "Task not found"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

