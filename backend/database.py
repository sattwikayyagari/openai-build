import sqlite3
from pathlib import Path

def init_db():
    Path("data").mkdir(exist_ok=True)
    conn= sqlite3.connect('data/storyloom.db')
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS books(book_id TEXT PRIMARY KEY, filename TEXT NOT NULL, file_contents TEXT NOT NULL, character_count INTEGER NOT NULL, created_at TEXT NOT NULL)")
        conn.commit()
    finally:
        conn.close()

def save_book(book_id: str, filename: str, file_contents: str, character_count:int, created_at:str):
    conn= sqlite3.connect('data/storyloom.db')
    params=(book_id,filename,file_contents,character_count,created_at)
    try:
        conn.execute("INSERT INTO books (book_id, filename,file_contents,character_count,created_at) VALUES (?,?,?,?,?)",params)
        conn.commit()
    finally:
        conn.close()

def get_book_details(book_id:str):
    conn=sqlite3.connect('data/storyloom.db')
    try:
        output=conn.execute("SELECT book_id, filename,file_contents, character_count, created_at FROM books where book_id=?",(book_id,)).fetchone()
        return output
    finally:
        conn.close()