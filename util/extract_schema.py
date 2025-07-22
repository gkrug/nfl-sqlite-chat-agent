import sqlite3

DB_PATH = 'data/pbp_db'
TABLE_NAME = 'nflfastR_pbp'
OUTPUT_PATH = 'schema/nflfastR_pbp_fields.txt'

def extract_schema(db_path, table_name, output_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f'PRAGMA table_info({table_name})')
    columns = cursor.fetchall()
    with open(output_path, 'w') as f:
        for col in columns:
            name = col[1]
            dtype = col[2]
            f.write(f'{name}: {dtype}\n')
    conn.close()

if __name__ == '__main__':
    extract_schema(DB_PATH, TABLE_NAME, OUTPUT_PATH)
    print(f'Schema written to {OUTPUT_PATH}') 