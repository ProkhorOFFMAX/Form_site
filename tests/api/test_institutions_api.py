import json

import pytest
# для кодирования кириллицы перед запросом
from urllib.parse import quote

import resource

from app import app
print([str(rule) for rule in app.url_map.iter_rules()])


@pytest.mark.parametrize("inst_type", ["ГБОУ", "ГБДОУ", "ОДОД"])
def test_get_institutions_success(client, seeded_institutions, inst_type):
    """Проверяет успешный ответ API для каждого типа ОУ"""
    response = client.get(f"/api/institutions/{inst_type}")  #
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 2
    for item in data:
        assert "id" in item
        assert "full_name" in item
        assert "short_name" in item

def test_get_institutions_invalid_type(client):
    response = client.get("/api/institutions/WRONG_E_TYPE")
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert data["error"] == 'Неверный тип'

def test_get_institutions_sorted(client):
    """Проверяет сортировку по short_name (для одного из типов)."""
    response = client.get("/api/institutions/ГБОУ")
    data = response.get_json()

    if len(data) > 1:
        names = [item["short_name"] for item in data]
        assert names == sorted(names)

def test_get_institutions_by_id(client, seeded_institutions):
    """Получение ОУ по ID"""
    response = client.get("/api/institutions/id/1")
    assert response.status_code == 200
    data = response.get_json()
    assert "id" in data
    assert "full_name" in data
    assert "short_name" in data
    assert "type" in data
    assert data["id"] == 1
    assert data["short_name"] == 'Школа №1'
    assert data["full_name"] == 'ГБОУ Школа №1'
    assert data["type"] == "ГБОУ"

def test_create_institutions(client):
    """Создвние ОУ"""
    response = client.post("/api/institutions", json={
        "full_name": "Тестовая школа",
        "short_name": "Тест",
        "type": "ГБОУ"
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert "id" in data
    assert data["id"] == 1

def test_edit_institutions_by_id(client, seeded_institutions):
    response = client.put("/api/institutions/1", json={
        "full_name": "Тестовая школа",
        "short_name": "Тест",
        "type": "ГБОУ"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True

def test_edit_institutions_not_exist(client):
    response = client.put("/api/institutions/1", json={
        "full_name": "Тестовая школа",
        "short_name": "Тест",
        "type": "ГБОУ"
    })
    assert response.status_code == 404
    data = response.get_json()
    assert data["success"] is False
    assert data["error"] == "ОУ не найдено"
