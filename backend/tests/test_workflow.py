from app.preferences.questions import QUESTIONS


def test_complete_backend_workflow(client):
    """Exercise registration through completion, re-login, persistence and edit resets."""
    token = client.get("/api/auth/csrf").json["csrf_token"]
    client.environ_base["HTTP_X_CSRF_TOKEN"] = token
    credentials = {"email": "workflow@example.com", "password": "workflow-password"}
    response = client.post("/api/auth/register", json=credentials)
    assert response.status_code == 201 and response.json["user"]["email"] == credentials["email"]
    assert client.post("/api/auth/login", json=credentials).status_code == 200
    fresh = client.get("/api/auth/csrf").json["csrf_token"]
    assert fresh != token
    client.environ_base["HTTP_X_CSRF_TOKEN"] = fresh
    assert client.patch("/api/profile", json={"full_name": "Workflow User"}).status_code == 200
    housing = {"city": "Seattle", "budget_min": "1000.00", "budget_max": "1500.00",
               "move_in_date": "2027-02-01", "lease_months": 12}
    assert client.patch("/api/preferences/housing", json=housing).status_code == 200
    for question in QUESTIONS:
        response = client.put("/api/preferences/lifestyle/" + question["question_key"], json={
            "own_answer": question["own_answers"][0], "roommate_answer": "no_preference", "is_requirement": False})
        assert response.status_code == 200
    state = client.get("/api/onboarding").json["onboarding"]
    assert state["eligible"] and not state["completed"]
    response = client.post("/api/onboarding/complete")
    assert response.status_code == 200 and response.json["onboarding"]["completed"]
    completed = response.json
    snapshots = {url: client.get(url).json for url in (
        "/api/profile", "/api/preferences/housing", "/api/preferences/lifestyle", "/api/onboarding")}
    assert client.post("/api/auth/logout").json == {"message": "Logged out."}
    assert client.get("/api/auth/me").status_code == 401
    client.environ_base["HTTP_X_CSRF_TOKEN"] = client.get("/api/auth/csrf").json["csrf_token"]
    assert client.post("/api/auth/login", json=credentials).status_code == 200
    client.environ_base["HTTP_X_CSRF_TOKEN"] = client.get("/api/auth/csrf").json["csrf_token"]
    for url, saved in snapshots.items():
        assert client.get(url).json == saved
    assert client.patch("/api/profile", json={"full_name": "Changed Name"}).status_code == 200
    assert client.get("/api/onboarding").json == completed
    assert client.patch("/api/preferences/housing", json={"city": None}).status_code == 200
    reset = client.get("/api/onboarding").json["onboarding"]
    assert not reset["completed"] and reset["onboarding_completed_at"] is None
    assert reset["missing_fields"] == ["housing.city"]
    assert client.patch("/api/preferences/housing", json={"city": "Seattle"}).status_code == 200
    restored = client.get("/api/onboarding").json["onboarding"]
    assert restored["eligible"] and not restored["completed"]
