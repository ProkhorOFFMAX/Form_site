import psycopg2
import pytest

def test_institutions_page_renders(client, seeded_institutions):
    response = client.get("/institutions")
    assert response.status_code == 200

    text = response.get_data(as_text=True)
    assert "Управление образовательными учреждениями" in text
    assert 'id="type-filter"' in text
    assert 'id="institutions-table"' in text
    # Проверяем, что в таблице есть данные (из seeded_institutions)
    assert "Школа №1" in text


def test_institutions_page_filters_by_type(client, seeded_institutions):
    """GET /institutions?type=ГБДОУ показывает только ГБДОУ."""
    response = client.get("/institutions?type=ГБДОУ")
    assert response.status_code == 200

    text = response.get_data(as_text=True)
    assert "Детсад №10" in text
    assert "Школа №1" not in text  # ГБОУ не должен отображаться

def test_create_institution_json_success(client, test_db_url):
    """POST /institutions/create с JSON создаёт запись и возвращает 201."""
    response = client.post("/institutions/create",
        json={
            "full_name": "Новая школа",
            "short_name": "Новая",
            "type": "ГБОУ"
        })
    assert response.status_code == 201
    assert response.get_json()["success"] is True

    conn = psycopg2.connect(test_db_url)
    with conn.cursor() as cur:
        cur.execute("SELECT full_name, short_name, type FROM educational_institutions WHERE short_name = 'Новая'")
        row = cur.fetchone()
    conn.close()
    assert row == ("Новая школа", "Новая", "ГБОУ")


def test_create_institution_json_invalid_type(client, test_db_url):
    """POST с неверным типом возвращает 400 и не создаёт запись."""
    response = client.post("/institutions/create",
                           json={
                               "full_name": "Тест",
                               "short_name": "Тест",
                               "type": "НЕВЕРНЫЙ"
                           })

    assert response.status_code == 400
    assert "error" in response.get_json()

    conn = psycopg2.connect(test_db_url)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM educational_institutions WHERE short_name = 'Тест'")
        count = cur.fetchone()[0]
    conn.close()
    assert count == 0


def test_delete_institution_success(client, seeded_institutions, test_db_url):
    """POST /institutions/delete/<id> удаляет запись."""
    # Получаем ID одного из ОУ
    conn = psycopg2.connect(test_db_url)
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM educational_institutions WHERE short_name = 'Школа №1'")
        inst_id = cur.fetchone()[0]
    conn.close()

    response = client.post(f"/institutions/delete/{inst_id}")
    assert response.status_code == 200
    assert response.get_json()["success"] is True

    # Проверяем, что запись удалена
    conn = psycopg2.connect(test_db_url)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM educational_institutions WHERE id = %s", (inst_id,))
        count = cur.fetchone()[0]
    conn.close()
    assert count == 0


def test_delete_nonexistent_institution(client):
    """POST /institutions/delete/99999 возвращает 404."""
    response = client.post("/institutions/delete/99999")
    print(response.get_data(as_text=True))
    assert response.status_code == 404
    assert "error" in response.get_json()


def test_edit_institution_success(client, seeded_institutions, test_db_url):
    """POST /institutions/edit/<id> обновляет запись."""
    # Получаем ID
    conn = psycopg2.connect(test_db_url)
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM educational_institutions WHERE short_name = 'Школа №1'")
        inst_id = cur.fetchone()[0]
    conn.close()

    response = client.post(f"/institutions/edit/{inst_id}",
                           json={
                               "full_name": "Обновлённая школа",
                               "short_name": "Обновлённая",
                               "type": "ГБДОУ"
                           })

    assert response.status_code == 200
    assert response.get_json()["success"] is True

    # Проверяем БД
    conn = psycopg2.connect(test_db_url)
    with conn.cursor() as cur:
        cur.execute("SELECT full_name, short_name, type FROM educational_institutions WHERE id = %s", (inst_id,))
        row = cur.fetchone()
    conn.close()
    assert row == ("Обновлённая школа", "Обновлённая", "ГБДОУ")


def test_edit_institution_invalid_data(client, seeded_institutions):
    """POST с пустым full_name возвращает 400."""
    response = client.post("/institutions/edit/1",
                           json={
                               "full_name": "",
                               "short_name": "Тест",
                               "type": "ГБОУ"
                           })
    print(response.get_data(as_text=True))


    assert response.status_code == 400
    assert "error" in response.get_json()