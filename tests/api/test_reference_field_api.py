import json
from urllib import response

import pytest

@pytest.mark.api
def test_create_reference_dict(client, test_db_url):
    response = client.post("/api/reference_dicts", json={"name": "Стихи Пушкина"})
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert isinstance(data["id"], int)

@pytest.mark.api
def test_create_reference_dict_empty(client, test_db_url):
    response = client.post("/api/reference_dicts", json={"name": " "})
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert data["error"] == "Название словаря обязательно"

@pytest.mark.api
def test_create_reference_dict_duplicate(client, test_db_url):
    client.post("/api/reference_dicts", json={"name": "duplicate"})
    resp = client.post("/api/reference_dicts", json={"name": "duplicate"})
    data = resp.get_json()
    assert resp.status_code == 400
    assert data["success"] is False
    assert data["error"] == "Словарь с таким названием уже существует"


@pytest.mark.api
def test_get_reference_items(client, test_db_url):
    resp = client.post("/api/reference_dicts", json={"name": "Стихи"})
    dict_id = resp.get_json()["id"]

    client.post("/api/reference_items", json={"dict_id": dict_id, "label": "Парус"})
    client.post("/api/reference_items", json={"dict_id": dict_id, "label": "Евгений Онегин"})

    response = client.get(f"/api/reference_items?dict_id={dict_id}")
    assert response.status_code == 200
    items = response.get_json()
    assert len(items) == 2
    assert items[0]["label"] == "Евгений Онегин"  # сортировка по label
    assert items[1]["label"] == "Парус"


@pytest.mark.api
def test_create_reference_item_duplicate(client, test_db_url):
    resp = client.post("/api/reference_dicts", json={"name": "Стихи"})
    dict_id = resp.get_json()["id"]

    client.post("/api/reference_items", json={"dict_id": dict_id, "label": "Парус"})
    response = client.post("/api/reference_items", json={"dict_id": dict_id, "label": "Парус"})
    assert response.status_code == 400