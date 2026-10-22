import psycopg2


def test_institutions_table_schema(test_db_url):
    conn = psycopg2.connect(test_db_url)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'educational_institutions'
                ORDER BY ordinal_position
            """)
            columns = dict(cur.fetchall())
    finally:
        conn.close()

    assert "id" in columns
    assert columns["full_name"] == "character varying"
    assert columns["short_name"] == "character varying"
    assert columns["type"] == "character varying"

def test_institutions_check_constraint(test_db_url):
    conn = psycopg2.connect(test_db_url)
    try:
        with conn.cursor() as cur:
            try:
                cur.execute("""
                INSERT INTO educational_institutions (full_name, short_name, type) 
                VALUES ('Тест', 'Тест', 'НЕВЕРНЫЙ')"""
                )
                conn.commit()
                assert False, "CHECK constraint не сработал"
            except psycopg2.errors.CheckViolation:
                conn.rollback()
    finally:
        conn.close()