# TexTexT/app/utils/database_operations.py

import psycopg2

def execute_query(query: str, query_type: str = 'fetchone', args = None):
    conn = None
    cursor = None
    
    try:
        conn = psycopg2.connect(
            host=app.config['DB_HOST'],
            database=app.config['DB_NAME'],
            user=app.config['DB_USERNAME'],
            password=app.config['DB_PASSWORD'],
            sslmode = "require"
        )

        cursor = conn.cursor()

        if args:
            cursor.execute(query, args)
        else:
            cursor.execute(query)
        
        if query_type == 'fetchone':
            result = cursor.fetchone()
        elif query_type == 'fetchall':
            result = cursor.fetchall()
        else:
            result = 'OK'

        conn.commit()

        return result
    except psycopg2.Error as e:
        print("Database error:", e)
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()