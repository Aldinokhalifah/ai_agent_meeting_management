import psycopg2
import psycopg2.extras
from core.config import DATABASE_URL

def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def execute_query(query: str, params: tuple = None, fetch: str = "all"):
    """
    Helper untuk eksekusi query
    fetch: "all", "one", "none"
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            conn.commit()

            if fetch == "all":
                result = cur.fetchall()
                return [dict(row) for row in result]
            elif fetch == "one":
                result = cur.fetchone()
                return dict(result) if result else None
            elif fetch == "none":
                return None

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()