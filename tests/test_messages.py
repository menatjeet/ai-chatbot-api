import pytest
from unittest.mock import patch


@pytest.fixture
def test_conversation(client, registered_user):
    res = client.post(
        "/api/conversations/",
        json={"title": "Test Chat"},
        headers=registered_user["headers"]
    )
    return res.json()


def test_create_message_success(client, registered_user, test_conversation):
    conv_id = test_conversation["id"]

    with patch("app.api.routes.messages.generate_ai_response") as mock_ai:
        mock_ai.return_value = ("FastAPI is a modern web framework.", "mock_interaction_1")

        payload = {"content": "What is FastAPI?"}
        response = client.post(
            f"/api/conversations/{conv_id}/messages",
            json=payload,
            headers=registered_user["headers"]
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user_message"]["content"] == payload["content"]
        assert data["user_message"]["role"] == "user"
        assert data["assistant_message"]["content"] == "FastAPI is a modern web framework."
        assert data["assistant_message"]["role"] == "assistant"

        # Verify AI function was called with conversation context
        mock_ai.assert_called_once()


def test_get_messages_history(client, registered_user, test_conversation):
    conv_id = test_conversation["id"]

    with patch("app.api.routes.messages.generate_ai_response") as mock_ai:
        mock_ai.return_value = ("Answer 1", "interaction_1")
        client.post(
            f"/api/conversations/{conv_id}/messages",
            json={"content": "Question 1"},
            headers=registered_user["headers"]
        )

        mock_ai.return_value = ("Answer 2", "interaction_2")
        client.post(
            f"/api/conversations/{conv_id}/messages",
            json={"content": "Question 2"},
            headers=registered_user["headers"]
        )

    # Fetch history
    history_res = client.get(
        f"/api/conversations/{conv_id}/messages",
        headers=registered_user["headers"]
    )
    assert history_res.status_code == 200
    messages = history_res.json()
    assert len(messages) == 4
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Question 1"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Answer 1"
    assert messages[2]["role"] == "user"
    assert messages[2]["content"] == "Question 2"
    assert messages[3]["role"] == "assistant"
    assert messages[3]["content"] == "Answer 2"


def test_stream_message_success(client, registered_user, test_conversation):
    conv_id = test_conversation["id"]

    def fake_stream(prompt, previous_interaction_id=None):
        yield ("text", "Hello ")
        yield ("text", "world!")
        yield ("completed", "interaction_stream_99")

    with patch("app.api.routes.messages.stream_ai_response", side_effect=fake_stream):
        response = client.post(
            f"/api/conversations/{conv_id}/messages/stream",
            json={"content": "Stream to me"},
            headers=registered_user["headers"]
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        body = response.text
        assert "user_message" in body
        assert "Hello " in body
        assert "world!" in body
        assert "done" in body

    # Verify assistant message was saved to database
    history_res = client.get(
        f"/api/conversations/{conv_id}/messages",
        headers=registered_user["headers"]
    )
    assert history_res.status_code == 200
    msgs = history_res.json()
    assert len(msgs) == 2
    assert msgs[1]["content"] == "Hello world!"
    assert msgs[1]["role"] == "assistant"


def test_create_message_conversation_not_found(client, registered_user):
    response = client.post(
        "/api/conversations/999999/messages",
        json={"content": "Nonexistent chat"},
        headers=registered_user["headers"]
    )
    assert response.status_code == 404


def test_messages_user_isolation(client, registered_user, second_user, test_conversation):
    conv_id = test_conversation["id"]

    # User 2 tries to send message to User 1's conversation
    res_post = client.post(
        f"/api/conversations/{conv_id}/messages",
        json={"content": "Unauthorized intrusion"},
        headers=second_user["headers"]
    )
    assert res_post.status_code == 404

    # User 2 tries to read messages from User 1's conversation
    res_get = client.get(
        f"/api/conversations/{conv_id}/messages",
        headers=second_user["headers"]
    )
    assert res_get.status_code == 404


def test_messages_ai_service_failure(client, registered_user, test_conversation):
    conv_id = test_conversation["id"]

    with patch("app.api.routes.messages.generate_ai_response") as mock_ai:
        mock_ai.side_effect = Exception("API rate limited or unreachable")

        response = client.post(
            f"/api/conversations/{conv_id}/messages",
            json={"content": "Trigger failure"},
            headers=registered_user["headers"]
        )
        assert response.status_code == 502
        assert "AI service is currently unavailable" in response.json()["detail"]
