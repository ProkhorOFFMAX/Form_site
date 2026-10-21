import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_database_url():
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    return (
        f"postgresql://{os.environ.get('DB_USER', 'form_user')}:"
        f"{os.environ.get('DB_PASSWORD', 'form_secret')}@"
        f"{os.environ.get('DB_HOST', 'localhost')}:"
        f"{os.environ.get('DB_PORT', '5432')}/"
        f"{os.environ.get('DB_NAME', 'form_db')}"
    )

def get_connection():
    """Возвращает новое соединение с БД."""
    return psycopg2.connect(os.environ["DATABASE_URL"])

def query_db(sql, params=None, fetch=True):
    """Универсальная функция для запросов

    fetch=True -> SELECT
    fetch=False -> INSERT/UPDATE/DELETE
    """

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            if fetch:
                return cur.fetchall()
            conn.commit()
    finally:
        conn.close()
