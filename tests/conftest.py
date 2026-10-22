import psycopg2
import pytest
import uuid
import os
import pathlib
from alembic.config import Config
from alembic import command

MIGRATIONS_DIR = pathlib.Path(__file__).parent.parent / "migrations"

from dotenv import load_dotenv

load_dotenv()

def apply_migrations(db_url):
    """Применяет все .sql-файлы из migrations/ по порядку."""
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
                cur.execute(sql_file.read_text(encoding="utf-8"))
    finally:
        conn.close()

@pytest.fixture(scope="session")
def test_db_url():
    """Создание временной БД на время тестовой сессии"""
    db_name = f"test_{uuid.uuid4().hex[:8]}"
    admin_url = (
        f"postgresql://{os.environ.get('DB_USER', 'test_user')}:"
        f"{os.environ.get('DB_PASSWORD', 'test_password')}@"
        f"{os.environ.get('DB_HOST', 'postgres')}:"
        f"{os.environ.get('DB_PORT', '5432')}/postgres"
    )

    # Создаём БД
    conn = psycopg2.connect(admin_url)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE {db_name}")
    conn.close()

    url = (
        f"postgresql://{os.environ.get('DB_USER', 'test_user')}:"
        f"{os.environ.get('DB_PASSWORD', 'test_password')}@"
        f"{os.environ.get('DB_HOST', 'postgres')}:"
        f"{os.environ.get('DB_PORT', '5432')}/"
        f"{db_name}"
    )




    alembic_cfg = Config("alembic.ini")
    alembic_cfg.attributes['connection_url'] = url
    command.upgrade(alembic_cfg, "head")

    yield url
    # Удаляем БД после тестов
    conn = psycopg2.connect(admin_url)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(f"DROP DATABASE {db_name}")
    conn.close()


@pytest.fixture
def app(test_db_url, monkeypatch):
    """Создаёт Flask-приложение с тестовой БД."""
    monkeypatch.setenv("DATABASE_URL", test_db_url)

    from app import app as flask_app
    flask_app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
    })

    yield flask_app

@pytest.fixture
def client(app):
    """Тестовый клиент Flask."""
    return app.test_client()

@pytest.fixture(autouse=True)
def clean_tables(test_db_url):
    """Очищает таблицы перед каждым тестом, чтобы данные не переносились."""
    conn = psycopg2.connect(test_db_url)
    with conn.cursor() as cur:
        cur.execute("TRUNCATE templates, responses RESTART IDENTITY CASCADE;")
    conn.commit()
    conn.close()