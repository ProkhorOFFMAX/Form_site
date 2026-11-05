import pytest
from click import option


@pytest.mark.api
def test_create_custom_field_success(client, test_db_url):
    response = client.post("/api/custom_fields", json={
        "label": "Город",
        "type": "select",
        "options": ["Москва", "Рязань"]
    })

    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert isinstance(data["id"], int)

    import psycopg2
    conn = psycopg2.connect(test_db_url)
    with conn.cursor() as cur:
        cur.execute("SELECT label, type FROM custom_fields WHERE id = %s",
                    (data["id"],))
        field = cur.fetchone()
        cur.execute("SELECT label FROM field_options WHERE field_id = %s ORDER BY sort_order", (data["id"],))
        options = [row[0] for row in cur.fetchall()]
    conn.close()
    assert field == ("Город", "select")
    assert options == ["Москва", "Рязань"]

@pytest.mark.api
def test_create_custom_field_empty_label(client):
    """Пустое значение -> 400"""
    response = client.post("/api/custom_fields", json={
        "label": "",
        "type": "select",
        "options": ["Москва"]
    })
    assert response.status_code == 400
    assert response.get_json()["success"] is False

@pytest.mark.api
def test_create_custom_field_empty_type(client):
    response = client.post("/api/custom_fields", json={
        "label": "Город",
        "type": "",
        "options": ["Москва"]
    })
    assert response.status_code == 400
    assert response.get_json()["success"] is False

@pytest.mark.api
def test_create_custom_field_empty_options(client):
    response = client.post("/api/custom_fields", json={
        "label": "Город",
        "type": "select",
        "options": []
    })
    assert response.status_code == 400
    assert response.get_json()["success"] is False


@pytest.mark.api
def test_get_custom_fields(client, test_db_url):
    """GET /api/custom_fields возвращает список."""
    # Создаём поле
    client.post("/api/custom_fields", json={
        "label": "Цвет",
        "type": "select",
        "options": ["Красный", "Синий"]
    })


    response = client.get("/api/custom_fields")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["label"] == "Цвет"

@pytest.mark.api
def test_create_custom_fields_duplicate(client, test_db_url):
    client.post("/api/custom_fields", json={
        "label": "Цвет",
        "type": "select",
        "options": ["Красный", "Синий"]
    })

    response = client.post("/api/custom_fields", json={
        "label": "Цвет",
        "type": "select",
        "options": ["Жёлтый", "Зелёный"]
    })

    assert response.status_code == 400