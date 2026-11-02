import sqlite3


def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS collections_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS video_collections (
            file_path TEXT PRIMARY KEY,
            collection_name TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()