import pytest


@pytest.mark.api
def test_create_user_as_admin(logged_in_admin, test_db_url):
    """Админ может создать пользователя."""
    # Логинимся как админ (нужен заранее созданный админ в тестовой БД)
    # ... (см. ниже, как создать админа в фикстуре) ...

    response = logged_in_admin.post("/admin/users/create", data={
        "email": "user@example.com",
        "password": "password123",
        "role": "user"
    }, follow_redirects=True)

    assert response.status_code == 200

    # Проверяем БД
    import psycopg2
    conn = psycopg2.connect(test_db_url)
    with conn.cursor() as cur:
        cur.execute("SELECT email, role FROM users WHERE email = 'user@example.com'")
        row = cur.fetchone()
    conn.close()

    assert row == ("user@example.com", "user")


@pytest.mark.api
def test_create_user_duplicate_email(logged_in_admin, test_db_url):
    """Повторный email → ошибка на странице, второй пользователь не создаётся."""
    # Первый раз — успешно
    logged_in_admin.post("/admin/users/create", data={
        "email": "dup@example.com",
        "password": "password123",
        "role": "user"
    }, follow_redirects=True)

    # Второй раз — тот же email
    response = logged_in_admin.post("/admin/users/create", data={
        "email": "dup@example.com",
        "password": "password456",
        "role": "user"
    })

    # Страница отрендерена (не редирект), код 200
    assert response.status_code == 200

    # В HTML есть сообщение об ошибке
    text = response.get_data(as_text=True)
    assert "уже существует" in text or "уже есть" in text

    # В БД только один пользователь с таким email
    import psycopg2
    conn = psycopg2.connect(test_db_url)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM users WHERE email = 'dup@example.com'")
        count = cur.fetchone()[0]
    conn.close()
    assert count == 1