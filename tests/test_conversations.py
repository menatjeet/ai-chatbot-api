def test_create_conversation(client, registered_user):
    payload = {"title": "Python Architecture Tips"}
    response = client.post(
        "/api/conversations/",
        json=payload,
        headers=registered_user["headers"]
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert "id" in data
    assert "created_at" in data


def test_get_conversations_list(client, registered_user):
    # Create two conversations
    client.post("/api/conversations/", json={"title": "Chat 1"}, headers=registered_user["headers"])
    client.post("/api/conversations/", json={"title": "Chat 2"}, headers=registered_user["headers"])

    response = client.get("/api/conversations/", headers=registered_user["headers"])
    assert response.status_code == 200
    chats = response.json()
    assert len(chats) >= 2
    titles = [c["title"] for c in chats]
    assert "Chat 1" in titles
    assert "Chat 2" in titles


def test_get_single_conversation(client, registered_user):
    res = client.post(
        "/api/conversations/",
        json={"title": "Specific Chat"},
        headers=registered_user["headers"]
    )
    conv_id = res.json()["id"]

    response = client.get(
        f"/api/conversations/{conv_id}",
        headers=registered_user["headers"]
    )
    assert response.status_code == 200
    assert response.json()["id"] == conv_id
    assert response.json()["title"] == "Specific Chat"


def test_update_conversation_title(client, registered_user):
    res = client.post(
        "/api/conversations/",
        json={"title": "Initial Title"},
        headers=registered_user["headers"]
    )
    conv_id = res.json()["id"]

    patch_res = client.patch(
        f"/api/conversations/{conv_id}",
        json={"title": "Renamed Conversation"},
        headers=registered_user["headers"]
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Renamed Conversation"


def test_delete_conversation(client, registered_user):
    res = client.post(
        "/api/conversations/",
        json={"title": "To Delete"},
        headers=registered_user["headers"]
    )
    conv_id = res.json()["id"]

    del_res = client.delete(
        f"/api/conversations/{conv_id}",
        headers=registered_user["headers"]
    )
    assert del_res.status_code == 204

    # Verify it is gone
    get_res = client.get(
        f"/api/conversations/{conv_id}",
        headers=registered_user["headers"]
    )
    assert get_res.status_code == 404


def test_conversation_user_isolation(client, registered_user, second_user):
    # User 1 creates a conversation
    res1 = client.post(
        "/api/conversations/",
        json={"title": "User 1 Secret"},
        headers=registered_user["headers"]
    )
    conv1_id = res1.json()["id"]

    # User 2 lists conversations: should NOT see User 1's conversation
    res2_list = client.get("/api/conversations/", headers=second_user["headers"])
    assert res2_list.status_code == 200
    assert not any(c["id"] == conv1_id for c in res2_list.json())

    # User 2 attempts to get User 1's conversation: should return 404
    res2_get = client.get(f"/api/conversations/{conv1_id}", headers=second_user["headers"])
    assert res2_get.status_code == 404

    # User 2 attempts to rename User 1's conversation: should return 404
    res2_patch = client.patch(
        f"/api/conversations/{conv1_id}",
        json={"title": "Hacked Title"},
        headers=second_user["headers"]
    )
    assert res2_patch.status_code == 404

    # User 2 attempts to delete User 1's conversation: should return 404
    res2_del = client.delete(f"/api/conversations/{conv1_id}", headers=second_user["headers"])
    assert res2_del.status_code == 404


def test_conversations_unauthorized(client):
    res = client.get("/api/conversations/")
    assert res.status_code == 401

    res_post = client.post("/api/conversations/", json={"title": "No Auth"})
    assert res_post.status_code == 401
