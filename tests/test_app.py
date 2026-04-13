"""
FastAPI tests for the Mergington High School Activities API.
Uses the Arrange-Act-Assert (AAA) pattern for test structure.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Provide a TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to a clean state before each test."""
    # Store original state
    original_activities = {}
    for name, details in activities.items():
        original_activities[name] = {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
    
    yield
    
    # Restore original state after test
    for name, details in original_activities.items():
        activities[name]["participants"] = details["participants"]


class TestGetActivities:
    """Tests for GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """
        Arrange: No setup needed, activities exist in app state
        Act: Make GET request to /activities
        Assert: Response status is 200 and contains expected activities
        """
        # Arrange
        expected_activities = {"Chess Club", "Programming Class", "Gym Class"}
        
        # Act
        response = client.get("/activities")
        returned_activities = response.json()
        
        # Assert
        assert response.status_code == 200
        assert isinstance(returned_activities, dict)
        for activity_name in expected_activities:
            assert activity_name in returned_activities
    
    def test_get_activities_returns_activity_details(self, client, reset_activities):
        """
        Arrange: No setup needed
        Act: Make GET request to /activities
        Assert: Response includes all required activity fields
        """
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        activities_data = response.json()
        
        # Assert
        assert response.status_code == 200
        for activity_name, activity_data in activities_data.items():
            assert all(field in activity_data for field in required_fields)
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_new_participant_success(self, client, reset_activities):
        """
        Arrange: Select Chess Club activity and new email
        Act: Send POST request to signup endpoint
        Assert: Response succeeds and confirms signup message
        """
        # Arrange
        activity_name = "Chess Club"
        new_email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {new_email} for {activity_name}"
    
    def test_signup_duplicate_registration_rejected(self, client, reset_activities):
        """
        Arrange: Select an activity and an existing participant
        Act: Send POST request to signup with duplicate email
        Assert: Response returns 400 error with appropriate message
        """
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()
    
    def test_signup_nonexistent_activity_returns_404(self, client, reset_activities):
        """
        Arrange: Use a non-existent activity name
        Act: Send POST request to signup endpoint
        Assert: Response returns 404 error with appropriate message
        """
        # Arrange
        nonexistent_activity = "Underwater Basket Weaving"
        test_email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup",
            params={"email": test_email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_adds_participant_to_activity(self, client, reset_activities):
        """
        Arrange: Select an activity and new email, record initial count
        Act: Send POST request to signup endpoint
        Assert: Participant count increases by one
        """
        # Arrange
        activity_name = "Gym Class"
        new_email = "newstudent@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 200
        assert len(activities[activity_name]["participants"]) == initial_count + 1
        assert new_email in activities[activity_name]["participants"]
    
    def test_signup_with_special_characters_in_activity_name(self, client, reset_activities):
        """
        Arrange: Use an activity name that needs URL encoding
        Act: Send POST request with encoded activity name
        Assert: Request succeeds and signup is confirmed
        """
        # Arrange
        activity_name = "Programming Class"
        new_email = "coder@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 200
        assert new_email in activities[activity_name]["participants"]
