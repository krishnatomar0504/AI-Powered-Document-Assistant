import sqlite3

from backend.config import DATA_DIR


DB_PATH = str(DATA_DIR / "documents.db")


def init_db():
    connection = sqlite3.connect(DB_PATH)

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            file_hash TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def reserve_document(file_hash, filename):
    connection = sqlite3.connect(DB_PATH)

    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO documents
        (file_hash, filename, status)
        VALUES (?, ?, ?)
    """, (file_hash, filename, "processing"))

    connection.commit()

    inserted = cursor.rowcount == 1

    connection.close()

    return inserted


def mark_indexed(file_hash):
    connection = sqlite3.connect(DB_PATH)

    cursor = connection.cursor()

    cursor.execute("""
        UPDATE documents
        SET status = ?
        WHERE file_hash = ?
    """, ("indexed", file_hash))

    connection.commit()
    connection.close()


def remove_document(file_hash):
    connection = sqlite3.connect(DB_PATH)

    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM documents WHERE file_hash = ?",
        (file_hash,)
    )

    connection.commit()
    connection.close()


init_db()