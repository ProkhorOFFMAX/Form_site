from pydoc import text

import pytest
import json


def _create_template_with_institution(client):
    response = client.post("/create", data={
        "name": "Анкета с ОУ",
        "fields_json": json.dumps([
            {"id": "f1", "label": "Учреждение", "type": "institution"}
        ])
    }, follow_redirects=True)
    assert response.status_code == 200
    return 1

def test_save_institution_valid_id(client, seeded_institutions):
    template_id = _create_template_with_institution(client)

    # Получить ID одного из ОУ (Первый ГБДОУ)
    response = client.get("/api/institutions/ГБОУ")
    institutions = response.get_json()
    inst_id = institutions[0]["id"]

    # заполнить анкету (Одно поле)
    response = client.post(f"/fill/{template_id}", data={
        "f1": str(inst_id)
    }, follow_redirects=True)
    assert response.status_code == 200

    from  db import query_db
    rows = query_db(
        "SELECT data FROM responses WHERE template_id = %s",
        (template_id,)
    )
    assert len(rows) == 1
    saved = rows[0]["data"]
    assert saved["f1"] == inst_id
    assert isinstance(saved["f1"], int)

def test_save_institution_invalid_id(client, seeded_institutions):
    template_id = _create_template_with_institution(client)

    response = client.post(f"/fill/{template_id}", data={
        "f1": str(999)
    }, follow_redirects=True)
    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "не найдено" in text or "не существует" in text

    from db import query_db
    rows = query_db(
        "SELECT id FROM responses WHERE template_id = %s",
        (template_id,)
    )
    assert len(rows) == 0, "Ответ с несуществующим ОУ не должен сохраняться"


def test_save_institution_empty_value(client, seeded_institutions):
    """Пустое значение отклоняется с ошибкой."""
    template_id = _create_template_with_institution(client)

    response = client.post(f"/fill/{template_id}", data={
        "f1": ""
    })
    assert response.status_code == 200
    assert "обязательно" in response.get_data(as_text=True)

    from db import query_db
    rows = query_db(
        "SELECT id FROM responses WHERE template_id = %s",
        (template_id,)
    )
    assert len(rows) == 0