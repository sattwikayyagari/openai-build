import sqlite3
from pathlib import Path
from uuid import uuid4 
from schemas import SceneBible,PlayableScene,SceneProgress
from datetime import datetime, timezone
from typing import List

def init_db():
    Path("data").mkdir(exist_ok=True)
    conn= sqlite3.connect('data/storyloom.db')
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS books(book_id TEXT PRIMARY KEY, filename TEXT NOT NULL, file_contents TEXT NOT NULL, character_count INTEGER NOT NULL, created_at TEXT NOT NULL)")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS chapters (chapter_id TEXT PRIMARY KEY, book_id TEXT NOT NULL, position INTEGER NOT NULL, source_number TEXT, title TEXT, content TEXT NOT NULL, UNIQUE(book_id,position), FOREIGN KEY(book_id) REFERENCES books(book_id))"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS scene_bibles (chapter_id TEXT PRIMARY KEY NOT NULL, scene_bible_json TEXT NOT NULL, created_at TEXT NOT NULL, FOREIGN KEY (chapter_id) REFERENCES chapters(chapter_id))"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS scene_progress (playthrough_id TEXT NOT NULL,chapter_id TEXT NOT NULL, progress_json TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY(playthrough_id,chapter_id), FOREIGN KEY (chapter_id) REFERENCES chapters(chapter_id))"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS playable_scenes (scene_id TEXT PRIMARY KEY NOT NULL,chapter_id TEXT NOT NULL, position INTEGER NOT NULL, scene_json TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(chapter_id,position), FOREIGN KEY (chapter_id) REFERENCES chapters(chapter_id))"
        )
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

def save_chapters(book_id: str, chapters: list):
    conn=sqlite3.connect('data/storyloom.db')
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        conn.execute("DELETE FROM chapters WHERE book_id=?",(book_id,))
        for chapter in chapters:
            chapter_id=str(uuid4())
            conn.execute("INSERT INTO chapters (chapter_id, book_id, position, source_number, title, content) VALUES (?,?,?,?,?,?)",(chapter_id,book_id,chapter['position'],chapter['source_number'],chapter['title'],chapter['content']))
        conn.commit()
    finally:
        conn.close()

def get_chapters(book_id:str)->list:
    conn=sqlite3.connect('data/storyloom.db')
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        chapter_metadata=conn.execute("SELECT chapter_id, position, source_number, title FROM chapters where book_id=? ORDER BY position",(book_id,)).fetchall()
        return chapter_metadata
    finally:
        conn.close()

def save_scene_bible(scene_bible:SceneBible):
    conn=sqlite3.connect('data/storyloom.db')
    conn.execute("PRAGMA foreign_keys=ON")

    try:
        chapter_id=scene_bible.chapter_id
        scene_bible_json=scene_bible.model_dump_json()
        created_at= datetime.now(timezone.utc).isoformat()
        conn.execute("INSERT INTO scene_bibles (chapter_id, scene_bible_json, created_at) VALUES (?,?,?) ON CONFLICT(chapter_id) DO UPDATE SET scene_bible_json=excluded.scene_bible_json, created_at=excluded.created_at",(chapter_id,scene_bible_json,created_at))
        conn.commit()
    finally:
        conn.close()

def get_scene_bible(chapter_id:str)->SceneBible|None:
    conn=sqlite3.connect('data/storyloom.db')
    try:
        output=conn.execute("SELECT scene_bible_json FROM scene_bibles where chapter_id=?",(chapter_id,)).fetchone()
        if output is None:
            return None
        scene_output=SceneBible.model_validate_json(output[0])
        return scene_output
    finally:
        conn.close()

def save_playable_scene(playable_scene:PlayableScene):
    conn=sqlite3.connect('data/storyloom.db')
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        scene_id=playable_scene.scene_id
        chapter_id=playable_scene.chapter_id
        position=playable_scene.position
        scene_json=playable_scene.model_dump_json()
        created_at=datetime.now(timezone.utc).isoformat()
        conn.execute("INSERT INTO playable_scenes (scene_id,chapter_id,position,scene_json,created_at) VALUES (?,?,?,?,?) ON CONFLICT(scene_id) DO UPDATE SET chapter_id=excluded.chapter_id, position=excluded.position, scene_json=excluded.scene_json, created_at=excluded.created_at",(scene_id,chapter_id,position,scene_json,created_at))
        conn.commit()
    finally:
        conn.close()       

def get_playable_scene(chapter_id:str)->PlayableScene|None:
    conn=sqlite3.connect('data/storyloom.db')
    try:
        output=conn.execute("SELECT scene_json FROM playable_scenes where chapter_id=?",(chapter_id,)).fetchone()
        if output is None:
            return None
        playable_scene=PlayableScene.model_validate_json(output[0])
        return playable_scene
    finally:
        conn.close()
    
def get_playable_scenes(chapter_id:str)->List[PlayableScene]:
    conn=sqlite3.connect('data/storyloom.db')
    data_rows=[]
    try:
        output=conn.execute("SELECT scene_json FROM playable_scenes WHERE chapter_id=? ORDER BY position",(chapter_id,)).fetchall()
        if not output:
            return []
        for row in output:
            playable_scene=PlayableScene.model_validate_json(row[0])
            data_rows.append(playable_scene)
        return data_rows
    finally:
        conn.close()
        
def save_scene_progress(scene_progress: SceneProgress):
    conn=sqlite3.connect('data/storyloom.db')
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        playthrough_id=scene_progress.playthrough_id
        chapter_id=scene_progress.chapter_id
        progress_json=scene_progress.model_dump_json()
        updated_at=datetime.now(timezone.utc).isoformat()
        conn.execute("INSERT INTO scene_progress (playthrough_id,chapter_id,progress_json,updated_at) VALUES (?,?,?,?) ON CONFLICT(playthrough_id,chapter_id) DO UPDATE SET progress_json=excluded.progress_json,updated_at=excluded.updated_at",(playthrough_id,chapter_id,progress_json,updated_at))
        conn.commit()
    finally:
        conn.close()

def get_scene_progress(playthrough_id:str, chapter_id:str)->SceneProgress|None:
    conn=sqlite3.connect('data/storyloom.db')
    try:
        progress_output=conn.execute("SELECT progress_json FROM scene_progress where playthrough_id=? AND chapter_id=?",(playthrough_id,chapter_id)).fetchone()
        if progress_output is None:
            return None
        scene_progress=SceneProgress.model_validate_json(progress_output[0])
        return scene_progress
    finally:
        conn.close()