"""
Comprehensive test suite for the Mergington High School FastAPI application.

Tests cover all endpoints with happy path, error cases, and edge cases:
- GET /
- GET /activities
- POST /activities/{activity_name}/signup
- DELETE /activities/{activity_name}/unregister
"""

import pytest


class TestRootEndpoint:
    """Tests for GET / endpoint (redirect to static HTML)."""
    
    def test_root_redirects_to_static_html(self, client):
        """Verify root endpoint redirects to /static/index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivitiesEndpoint:
    """Tests for GET /activities endpoint."""
    
    def test_get_activities_returns_dict(self, client, reset_activities):
        """Verify GET /activities returns activities as a dictionary."""
        response = client.get("/activities")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)
    
    def test_get_activities_contains_expected_activities(self, client, reset_activities):
        """Verify response contains all expected activities."""
        response = client.get("/activities")
        activities_data = response.json()
        
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Tennis Club",
            "Drama Club",
            "Art Studio",
            "Debate Team",
            "Science Club"
        ]
        
        for activity_name in expected_activities:
            assert activity_name in activities_data
    
    def test_activity_has_required_fields(self, client, reset_activities):
        """Verify each activity has description, schedule, max_participants, and participants."""
        response = client.get("/activities")
        activities_data = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity_data in activities_data.items():
            for field in required_fields:
                assert field in activity_data, f"Activity '{activity_name}' missing '{field}'"
    
    def test_participants_list_is_list_of_strings(self, client, reset_activities):
        """Verify participants field contains email strings."""
        response = client.get("/activities")
        activities_data = response.json()
        
        for activity_name, activity_data in activities_data.items():
            assert isinstance(activity_data["participants"], list)
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant  # Basic email validation


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_success(self, client, reset_activities, new_participant_email):
        """Verify successful signup adds email to participants list."""
        activity_name = "Chess Club"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_participant_email}
        )
        
        assert response.status_code == 200
        assert "signed up" in response.json()["message"].lower()
        assert new_participant_email in response.json()["message"]
        assert activity_name in response.json()["message"]
    
    def test_signup_adds_email_to_participants(self, client, reset_activities, new_participant_email):
        """Verify email is actually added to activity's participants."""
        activity_name = "Programming Class"
        
        # Signup
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_participant_email}
        )
        assert response.status_code == 200
        
        # Verify in activities
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert new_participant_email in activities_data[activity_name]["participants"]
    
    def test_signup_already_signed_up_returns_400(self, client, reset_activities):
        """Verify signup fails with 400 if email already registered for activity."""
        activity_name = "Chess Club"
        # This activity already has michael@mergington.edu as participant
        existing_email = "michael@mergington.edu"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )
        
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()
    
    def test_signup_nonexistent_activity_returns_404(self, client, reset_activities, new_participant_email):
        """Verify signup fails with 404 for nonexistent activity."""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": new_participant_email}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_multiple_activities(self, client, reset_activities, new_participant_email):
        """Verify same email can signup for multiple activities."""
        activities_to_join = ["Chess Club", "Basketball Team", "Drama Club"]
        
        for activity_name in activities_to_join:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": new_participant_email}
            )
            assert response.status_code == 200
        
        # Verify signup for all activities
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        for activity_name in activities_to_join:
            assert new_participant_email in activities_data[activity_name]["participants"]
    
    @pytest.mark.parametrize("activity_name", [
        "Chess Club",
        "Programming Class",
        "Gym Class",
        "Basketball Team"
    ])
    def test_signup_various_activities(self, client, reset_activities, new_participant_email, activity_name):
        """Parametrized test: verify signup works for various activities."""
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_participant_email}
        )
        
        assert response.status_code == 200
        assert activity_name in response.json()["message"]


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_success(self, client, reset_activities):
        """Verify successful unregister removes email from participants."""
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"  # Already in Chess Club
        
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email_to_remove}
        )
        
        assert response.status_code == 200
        assert "unregistered" in response.json()["message"].lower()
        assert email_to_remove in response.json()["message"]
        assert activity_name in response.json()["message"]
    
    def test_unregister_removes_from_participants(self, client, reset_activities):
        """Verify email is actually removed from activity's participants."""
        activity_name = "Programming Class"
        email_to_remove = "emma@mergington.edu"  # Already in Programming Class
        
        # Verify email is in activity before unregister
        activities_before = client.get("/activities").json()
        assert email_to_remove in activities_before[activity_name]["participants"]
        
        # Unregister
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email_to_remove}
        )
        assert response.status_code == 200
        
        # Verify email removed from participants
        activities_after = client.get("/activities").json()
        assert email_to_remove not in activities_after[activity_name]["participants"]
    
    def test_unregister_not_signed_up_returns_400(self, client, reset_activities, test_email):
        """Verify unregister fails with 400 if email not registered for activity."""
        activity_name = "Chess Club"
        
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": test_email}
        )
        
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()
    
    def test_unregister_nonexistent_activity_returns_404(self, client, reset_activities, test_email):
        """Verify unregister fails with 404 for nonexistent activity."""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister",
            params={"email": test_email}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_then_unregister(self, client, reset_activities, new_participant_email):
        """Verify signup followed by unregister correctly manages participant state."""
        activity_name = "Tennis Club"
        
        # Signup
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_participant_email}
        )
        assert signup_response.status_code == 200
        
        # Verify in participants
        activities_after_signup = client.get("/activities").json()
        assert new_participant_email in activities_after_signup[activity_name]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": new_participant_email}
        )
        assert unregister_response.status_code == 200
        
        # Verify removed from participants
        activities_after_unregister = client.get("/activities").json()
        assert new_participant_email not in activities_after_unregister[activity_name]["participants"]
    
    def test_unregister_multiple_times_second_fails(self, client, reset_activities):
        """Verify second unregister attempt fails after first successful unregister."""
        activity_name = "Debate Team"
        email = "aiden@mergington.edu"
        
        # First unregister should succeed
        response1 = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second unregister should fail
        response2 = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        assert response2.status_code == 400
        assert "not signed up" in response2.json()["detail"].lower()
