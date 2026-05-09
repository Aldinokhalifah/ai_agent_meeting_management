from db.postgres import execute_query

try:
    result = execute_query("SELECT NOW()", fetch="one")
    print("✅ Database connected:", result)
except Exception as e:
    print("❌ Database error:", e)