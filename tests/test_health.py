def test_home_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "AI Chatbot API" in data["message"]
    assert data["docs_url"] == "/docs"
    assert data["chat_ui"] == "/chat"


def test_health_check_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_db_check_endpoint(client):
    response = client.get("/db-check")
    assert response.status_code == 200
    data = response.json()
    assert data["database"] == "connected"
    assert data["status"] == "success"


def test_chat_ui_endpoint(client):
    response = client.get("/chat")
    assert response.status_code == 200
    assert "ApexAI" in response.text
    assert "messagesContainer" in response.text
