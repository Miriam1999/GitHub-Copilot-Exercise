from urllib.parse import quote

from fastapi.testclient import TestClient

from src import app as app_module


client = TestClient(app_module.app)


def test_get_activities_returns_activity_details():
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert expected_activity in response.json()
    assert set(response.json()[expected_activity]) == {
        "description",
        "schedule",
        "max_participants",
        "participants",
    }


def test_root_redirects_to_static_index():
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_signup_registers_participant():
    # Arrange
    activity = "Soccer Club"
    email = "student@example.com"

    # Act
    response = client.post(f"/activities/{quote(activity)}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity}"}
    assert email in app_module.activities[activity]["participants"]


def test_signup_supports_url_encoded_activity_and_email():
    # Arrange
    activity = "Chess Club"
    email = "student+club@example.com"

    # Act
    response = client.post(
        f"/activities/{quote(activity)}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert email in app_module.activities[activity]["participants"]


def test_signup_rejects_unknown_activity():
    # Arrange
    activity = "Unknown Club"
    email = "student@example.com"

    # Act
    response = client.post(f"/activities/{quote(activity)}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_unknown_activity():
    # Arrange
    activity = "Unknown Club"
    email = "student@example.com"

    # Act
    response = client.delete(f"/activities/{quote(activity)}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant():
    # Arrange
    activity = "Chess Club"
    email = app_module.activities[activity]["participants"][0]
    original_count = app_module.activities[activity]["participants"].count(email)

    # Act
    response = client.post(f"/activities/{quote(activity)}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert app_module.activities[activity]["participants"].count(email) == original_count


def test_unregister_removes_participant():
    # Arrange
    activity = "Chess Club"
    email = app_module.activities[activity]["participants"][0]

    # Act
    response = client.delete(f"/activities/{quote(activity)}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity}"}
    assert email not in app_module.activities[activity]["participants"]


def test_unregister_rejects_participant_who_is_not_registered():
    # Arrange
    activity = "Soccer Club"
    email = "student@example.com"

    # Act
    response = client.delete(f"/activities/{quote(activity)}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_signup_rejects_full_activity():
    # Arrange
    activity = "Soccer Club"
    participants = app_module.activities[activity]["participants"]
    max_participants = app_module.activities[activity]["max_participants"]
    participants.extend(f"student{index}@example.com" for index in range(max_participants))
    email = "new-student@example.com"

    # Act
    response = client.post(f"/activities/{quote(activity)}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"
    assert len(participants) == max_participants
    assert email not in participants


def test_signup_rejects_invalid_email():
    # Arrange
    activity = "Soccer Club"
    email = "not-an-email"

    # Act
    response = client.post(f"/activities/{quote(activity)}/signup", params={"email": email})

    # Assert
    assert response.status_code == 422
    assert "email" in response.json()["detail"][0]["loc"]
