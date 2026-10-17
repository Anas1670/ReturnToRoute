import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return psycopg.connect(
        dbname=os.getenv("DB_NAME", "return_to_route"),
        user=os.getenv("DB_USER") or os.getlogin(),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        password=os.getenv("DB_PASSWORD") or None
    )
