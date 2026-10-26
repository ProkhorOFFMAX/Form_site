import json
from urllib import response


def test_index_empty(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Пока нет ни одного шаблона" in response.get_data(as_text=True)


def test_create_template(client):
    response = client.post("/create", data={
        "name": "Тестовая анкета",
        "fields_json": json.dumps([
            {"id": "f1", "label": "Имя", "type": "text"}
        ])
    }, follow_redirects=True)

    assert response.status_code == 200
    assert "Тестовая анкета" in response.get_data(as_text=True)


def test_create_template_validation(client):
    response = client.post("/create", data={
        "name": "",
        "fields_json": "[]"
    })

    assert response.status_code == 200
    assert "Название обязательно" in response.get_data(as_text=True)


def test_fill_and_view(client):
    # Создаём шаблон
    client.post("/create", data={
        "name": "Анкета",
        "fields_json": json.dumps([
            {"id": "f1", "label": "Имя", "type": "text"},
            {"id": "f2", "label": "Возраст", "type": "number"},
            {"id": "f3", "label": "ОВЗ", "type": "boolean"}

        ])
    })

    # Заполняем
    response = client.post("/fill/1", data={
        "f1": "Иван",
        "f2": "30",
        "f3": "true"
    }, follow_redirects=True)

    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert "Иван" in text
    assert "30" in text
    assert "Да" in text

def test_institution(client):
    response = client.get("/institutions", data={})
    assert response.status_code == 200
