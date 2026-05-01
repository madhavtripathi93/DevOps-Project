import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Ansb6004")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "agent_marketplace")

def migrate_db():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()
        
        # Check if username column exists
        cursor.execute("SHOW COLUMNS FROM users LIKE 'username'")
        result = cursor.fetchone()
        
        if not result:
            print("Adding 'username' column to 'users' table...")
            cursor.execute("ALTER TABLE users ADD COLUMN username VARCHAR(50) UNIQUE AFTER id")
            conn.commit()
            print("Migration successful.")
        else:
            print("'username' column already exists.")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Migration error: {e}")

if __name__ == "__main__":
    migrate_db()
