from db.postgres import execute_query

def test_connection():
    try:
        result = execute_query("SELECT NOW()", fetch="one")
        return {
            "status": "ok",
            "message": "Database connected",
            "data": result,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database connection failed: {str(e)}",
        }