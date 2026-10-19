import os
import psycopg2
from psycopg2.extras import RealDictCursor

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
