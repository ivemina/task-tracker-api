def test_create_and_list_task(client, auth_headers):
    headers = auth_headers("a@example.com")
    created = client.post("/tasks", json={"title": "Write tests"}, headers=headers)
    assert created.status_code == 201

    listed = client.get("/tasks", headers=headers)
    assert [task["title"] for task in listed.json()] == ["Write tests"]


def test_user_cannot_see_other_users_tasks(client, auth_headers):
    headers_a = auth_headers("a@example.com")
    headers_b = auth_headers("b@example.com")
    task_id = client.post(
        "/tasks", json={"title": "A's task"}, headers=headers_a
    ).json()["id"]

    assert client.get("/tasks", headers=headers_b).json() == []
    assert client.get(f"/tasks/{task_id}", headers=headers_b).status_code == 404

def test_user_cannot_delete_other_users_task(client, auth_headers):
    headers_a = auth_headers("a@example.com")
    headers_b = auth_headers("b@example.com")
    task_id = client.post(
        "/tasks", json={"title": "A's task"}, headers=headers_a
    ).json()["id"]

    response = client.delete(f"/tasks/{task_id}", headers=headers_b)
    assert response.status_code == 404

    still_there = client.get(f"/tasks/{task_id}", headers=headers_a)
    assert still_there.status_code == 200