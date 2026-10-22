import pytest
# для кодирования кириллицы перед запросом
from urllib.parse import quote
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