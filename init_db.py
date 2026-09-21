import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

def init_db():
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    
    try:
        with conn.cursor() as cur:
            # 1. InputLogs
            cur.execute("""
                CREATE TABLE IF NOT EXISTS InputLogs (
                    id SERIAL PRIMARY KEY,
                    raw_input TEXT NOT NULL,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    rows_extracted INTEGER[]
                )
            """)
            
            # 2. Knowledge
            cur.execute("""
                CREATE TABLE IF NOT EXISTS Knowledge (
                    id SERIAL PRIMARY KEY,
                    category VARCHAR(50) NOT NULL,
                    quote TEXT,
                    author TEXT,
                    event TEXT,
                    date TEXT,
                    command TEXT,
                    description TEXT,
                    last_review TIMESTAMP,
                    next_review TIMESTAMP,
                    stability FLOAT,
                    difficulty FLOAT
                )
            """)
            
            # 3. Test
            cur.execute("""
                CREATE TABLE IF NOT EXISTS Test (
                    id SERIAL PRIMARY KEY,
                    id_knowledge INTEGER REFERENCES Knowledge(id) ON DELETE CASCADE,
                    grade INTEGER CHECK (grade IN (1, 2, 3, 4)),
                    feedback TEXT,
                    self_grade INTEGER CHECK (self_grade IN (1, 2, 3, 4))
                )
            """)
            print("Database tables initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()