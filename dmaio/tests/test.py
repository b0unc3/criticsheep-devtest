import unittest
from fastapi.testclient import TestClient
from app.main import app, get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./elevator.db" 
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

class TestAPI(unittest.TestCase):
    def test_create_elevator(self):
        response = client.post("/elevators/", json={"name": "Elevator Test", "location": "Building Test"})
        self.assertEqual(response.status_code, 200)
    
    def test_log_movement(self):
        response = client.post("/movements/", 
                json={
                    "elevator_id": 1, 
                    "start_floor": 1, 
                    "end_floor": 2,
                    })
        self.assertEqual(response.status_code, 200)

    def test_get_movements(self):
        response = client.get("/movements/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

if __name__ == "__main__":
    unittest.main()
