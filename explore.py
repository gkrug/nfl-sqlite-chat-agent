import sqlite3
import os

DB_PATH = os.path.join("data", "pbp_db")  # Adjust if you're running from a different location
SCHEMA_OUTPUT_PATH = "schema_context.txt"

def extract_schema(db_path: str, output_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    with open(output_path, "w") as f:
        for table in tables:
            f.write(f"-- {table} --\n")
            cursor.execute(f"PRAGMA table_info({table});")
            for col in cursor.fetchall():
                col_name = col[1]
                col_type = col[2]
                f.write(f"{col_name}: {col_type}\n")
            f.write("\n")

    conn.close()
    print(f"✅ Schema written to {output_path}")

if __name__ == "__main__":
    extract_schema(DB_PATH, SCHEMA_OUTPUT_PATH)
