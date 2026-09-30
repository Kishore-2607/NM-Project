import os
import pytest

os.environ["MOCK_AI"] = "true"

from fastapi.testclient import TestClient
from app.database import Base, engine, SessionLocal, User, WorkoutPlan
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "FitBuddy" in response.text
    assert "Generate Plan" in response.text
    assert "Fitness Goal:" in response.text
    assert "Workout Intensity:" in response.text


def test_web_generate_workout_and_view_result():
    response = client.post(
        "/generate-workout",
        data={
            "name": "Shreya",
            "user_id": "1",
            "age": "22",
            "weight": "55.0",
            "goal": "muscle gain",
            "intensity": "High",
        },
    )
    assert response.status_code == 200
    html = response.text
    assert "Your Personalized Workout Plan" in html
    assert "Shreya" in html
    assert "55.0 kg" in html
    assert "muscle gain" in html
    assert "Workout Plan" in html
    assert "Nutrition Tip" in html
    assert "Share Your Feedback" in html


def test_web_submit_feedback_updates_plan():
    # First generate workout
    client.post(
        "/generate-workout",
        data={
            "name": "Shreya",
            "user_id": "1",
            "age": "22",
            "weight": "55.0",
            "goal": "muscle gain",
            "intensity": "High",
        },
    )

    # Now submit feedback
    response = client.post(
        "/submit-feedback",
        data={
            "user_id": "1",
            "feedback": "Include more yoga and cardio on rest days.",
        },
    )
    assert response.status_code == 200
    html = response.text
    assert "Your plan has been updated based on your feedback!" in html
    assert "Updated Workout Plan" in html


def test_admin_view_all_users():
    # Insert user and plan
    client.post(
        "/generate-workout",
        data={
            "name": "Shreya",
            "user_id": "1",
            "age": "22",
            "weight": "55.0",
            "goal": "muscle gain",
            "intensity": "High",
        },
    )

    response = client.get("/view-all-users")
    assert response.status_code == 200
    html = response.text
    assert "FitBuddy - All Users &amp; Workout Plans" in html or "FitBuddy - All Users & Workout Plans" in html
    assert "Shreya" in html
    assert "muscle gain" in html


def test_admin_delete_user():
    # Create user
    client.post(
        "/generate-workout",
        data={
            "name": "To Delete",
            "user_id": "99",
            "age": "30",
            "weight": "80",
            "goal": "weight loss",
            "intensity": "Low",
        },
    )

    # Delete user
    del_resp = client.post("/delete-user/99", follow_redirects=True)
    assert del_resp.status_code == 200
    assert "To Delete" not in del_resp.text


def test_doc_api_generate_workout_gemini():
    response = client.post(
        "/generate-workout/gemini",
        json={"goal": "weight loss", "intensity": "high"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "gemini-pro"
    assert "workout_plan" in data
    assert len(data["workout_plan"]) > 50


def test_doc_api_nutrition_tip():
    response = client.get("/nutrition-tip?goal=muscle+gain")
    assert response.status_code == 200
    data = response.json()
    assert data["goal"] == "muscle gain"
    assert "nutrition_tip" in data
    assert len(data["nutrition_tip"]) > 10


def test_doc_api_generate_plan():
    response = client.post(
        "/generate-plan",
        json={
            "user_id": "10",
            "username": "xyz",
            "age": 20,
            "weight": 70.0,
            "goal": "i want to lose belly fat and gain muscles",
            "intensity": "High",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "Workout plan generated and saved successfully!" in data["message"]
    assert "workout_plan" in data


def test_doc_api_update_plan():
    # Save plan first
    client.post(
        "/generate-plan",
        json={
            "user_id": "10",
            "username": "xyz",
            "age": 20,
            "weight": 70.0,
            "goal": "muscle gain",
            "intensity": "High",
        },
    )

    response = client.post(
        "/update-plan/10",
        json={"feedback": "Add more core work"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "updated_plan" in data


def test_api_generate_and_feedback():
    gen_resp = client.post(
        "/api/generate-workout",
        json={
            "name": "Test User",
            "user_id": "test01",
            "age": 25,
            "weight": 70,
            "goal": "muscle gain",
            "intensity": "medium",
        },
    )
    assert gen_resp.status_code == 200
    assert gen_resp.json()["user_id"] == "test01"

    feed_resp = client.post(
        "/api/submit-feedback",
        json={
            "user_id": "test01",
            "feedback": "Add more cardio",
        },
    )
    assert feed_resp.status_code == 200
    assert feed_resp.json()["updated_plan"]

    users_resp = client.get("/api/users")
    assert users_resp.status_code == 200
    assert len(users_resp.json()["users"]) >= 1
