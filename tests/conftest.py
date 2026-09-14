"""
Shared pytest fixtures for FastAPI tests.

This module provides reusable fixtures for testing the Mergington High School API,
including the TestClient and sample test data.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """
    Provide a TestClient for the FastAPI application.
    
    Returns a fresh TestClient instance for each test.
    """
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """
    Reset activities to initial state before and after each test.
    
    This ensures tests don't interfere with each other due to shared
    in-memory state in the activities dictionary.
    
    Yields control to test, then resets activities after test completes.
    """
    # Store original state
    original_activities = {
        name: {
            "description": activity["description"],
            "schedule": activity["schedule"],
            "max_participants": activity["max_participants"],
            "participants": activity["participants"].copy()
        }
        for name, activity in activities.items()
    }
    
    yield
    
    # Reset to original state after test
    activities.clear()
    activities.update(original_activities)


@pytest.fixture
def test_email():
    """Provide a test email address for signup/unregister operations."""
    return "test_student@mergington.edu"


@pytest.fixture
def new_participant_email():
    """Provide a new participant email for testing signup."""
    return "new_participant@mergington.edu"
