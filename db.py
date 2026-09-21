import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

def insert_approved_items(raw_input: str, items: list[dict]) -> None:
    if not items:
        return
        
    conn = psycopg2.connect(DB_URL)
    try:
        with conn.cursor() as cur:
            inserted_ids = []
            
            # 1. Insert into Knowledge and collect IDs
            insert_query = """
                INSERT INTO Knowledge (category, quote, author, event, date, command, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            
            for item in items:
                cur.execute(insert_query, (
                    item.get("category"),
                    item.get("quote"),
                    item.get("author"),
                    item.get("event"),
                    item.get("date"),
                    item.get("command"),
                    item.get("description")
                ))
                inserted_ids.append(cur.fetchone()[0])
            
            # 2. Insert into InputLogs with the array of foreign keys
            log_query = """
                INSERT INTO InputLogs (raw_input, rows_extracted)
                VALUES (%s, %s)
            """
            cur.execute(log_query, (raw_input, inserted_ids))
            
            conn.commit()
            print(f"\n[Database] Successfully saved {len(items)} items and updated InputLogs.")
            
    except Exception as e:
        conn.rollback()
        print(f"\n[Database] Error saving to Postgres: {e}")
        raise e
    finally:
        conn.close()