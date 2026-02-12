"""
Tests for the FastAPI Activities Management System
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Fixture for FastAPI test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities before each test to ensure clean state"""
    from src.app import activities
    
    # Store original state
    original = activities.copy()
    
    # Reset to fresh state
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": []
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": []
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": []
        }
    })
    
    yield
    
    # Restore original state
    activities.clear()
    activities.update(original)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all available activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_returns_activity_details(self, client):
        """Test that activities include necessary details"""
        response = client.get("/activities")
        data = response.json()
        chess = data["Chess Club"]
        
        assert "description" in chess
        assert "schedule" in chess
        assert "max_participants" in chess
        assert "participants" in chess
        assert isinstance(chess["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_activity_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=student@school.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
    
    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant"""
        client.post("/activities/Chess Club/signup?email=student@school.edu")
        response = client.get("/activities")
        activities = response.json()
        assert "student@school.edu" in activities["Chess Club"]["participants"]
    
    def test_signup_duplicate_student_error(self, client):
        """Test that duplicate signup is rejected"""
        # First signup
        response1 = client.post(
            "/activities/Chess Club/signup?email=student@school.edu"
        )
        assert response1.status_code == 200
        
        # Duplicate signup
        response2 = client.post(
            "/activities/Chess Club/signup?email=student@school.edu"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
    
    def test_signup_nonexistent_activity_error(self, client):
        """Test that signup for nonexistent activity fails"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@school.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_multiple_students(self, client):
        """Test that multiple students can sign up for the same activity"""
        email1 = "student1@school.edu"
        email2 = "student2@school.edu"
        
        response1 = client.post(f"/activities/Chess Club/signup?email={email1}")
        response2 = client.post(f"/activities/Chess Club/signup?email={email2}")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify both are registered
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert email1 in participants
        assert email2 in participants


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""
    
    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        email = "student@school.edu"
        
        # First signup
        client.post(f"/activities/Chess Club/signup?email={email}")
        
        # Then unregister
        response = client.delete(
            f"/activities/Chess Club/participants/{email}"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
    
    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        email = "student@school.edu"
        
        # Signup
        client.post(f"/activities/Chess Club/signup?email={email}")
        
        # Verify signup
        response1 = client.get("/activities")
        assert email in response1.json()["Chess Club"]["participants"]
        
        # Unregister
        client.delete(f"/activities/Chess Club/participants/{email}")
        
        # Verify removal
        response2 = client.get("/activities")
        assert email not in response2.json()["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_participant_error(self, client):
        """Test that unregistering a non-participant fails"""
        response = client.delete(
            "/activities/Chess Club/participants/notregistered@school.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_unregister_nonexistent_activity_error(self, client):
        """Test that unregistering from nonexistent activity fails"""
        response = client.delete(
            "/activities/Nonexistent Club/participants/student@school.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestRootRedirect:
    """Tests for root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root path redirects to static index"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers.get("location", "")
