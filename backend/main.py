from fastapi import FastAPI, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from uuid import uuid4
from database import init_db, save_book,save_playable_scene, get_book_details, get_chapters, save_chapters, get_scene_bible, get_playable_scene,get_playable_scenes, get_scene_progress, save_scene_progress
from datetime import timezone, datetime
from chapter_splitter import split_chapters
from schemas import SceneBible, PlayableScene,SceneProgress,SceneGenerationRequest
from typing import List
# from scene_generator import generate_playable_scene
from scene_generator import generate_scene_plan
from scene_builder import build_playable_scene_from_plan
from chapter_pipeline import generate_playable_chapter

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    
app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_headers=["*"],
    allow_methods=["*"],
    allow_credentials=False
)



@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/books")
async def upload_books(file: UploadFile):
   file_name= file.filename
   if not file_name:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="File name not found")
   if not file_name.lower().endswith(".txt"):
       raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="File type not supported")
   file_contents=await file.read()
   if not file_contents:
       raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File contents not found")
   try:
        text=file_contents.decode('utf-8')
   except UnicodeDecodeError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="File contents cannot be decoded")
   book_id=str(uuid4())
   created_at=datetime.now(timezone.utc).isoformat()
   save_book(
       book_id=book_id,
       filename=file_name,
       file_contents=text,
       character_count=len(text),
       created_at=created_at)
   return {
    "book_id": book_id,
    "filename": file_name,
    "character_count": len(text),
    "preview": text[:200],
}

@app.get("/books/{book_id}")
def get_book_details_by_id(book_id: str):
    book_details=get_book_details(book_id)
    if not book_details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book Not found")
    stored_book_id,stored_filename,stored_file_contents,stored_char_count,stored_creation_time=book_details
    return {
        "book_id":stored_book_id,
        "filename": stored_filename,
        "character_count": stored_char_count,
        "created_at": stored_creation_time,
        "preview": stored_file_contents[:200]
        }

@app.get("/books/{book_id}/chapters")
def get_chapters_by_id(book_id: str)->list:
    chapter_metalist=[]
    book_details=get_book_details(book_id)
    if book_details is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book Not Found")
    rows=get_chapters(book_id)
    for row in rows:
        chapter_dict={}
        chapter_dict["chapter_id"]=row[0]
        chapter_dict["position"]=row[1]
        chapter_dict["source_number"]=row[2]
        chapter_dict["title"]=row[3]
        chapter_metalist.append(chapter_dict)
    return chapter_metalist

@app.post("/books/{book_id}/chapters")
def  split_book_chapters(book_id:str)->dict:
    book_details=get_book_details(book_id)
    if book_details is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book Not Found")
    stored_book_id,stored_filename,stored_filecontents,stored_char_count,stored_time=book_details
    chapter_list=split_chapters(stored_filecontents)
    if not chapter_list:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,detail="Chapters not found")
    save_chapters(book_id,chapter_list)
    return {
        "book_id": book_id,
        "chapter_count": len(chapter_list)
    }

@app.get("/chapters/{chapter_id}/scene-bible")
def get_scene_bible_by_id(chapter_id: str)->SceneBible:
    scene_bible_output=get_scene_bible(chapter_id)
    if scene_bible_output is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Scene Bible not found")
    return scene_bible_output

@app.get("/chapters/{chapter_id}/playable-scene")
def get_playable_scene_by_id(chapter_id: str)->PlayableScene:
    playable_scene_output=get_playable_scene(chapter_id)
    if playable_scene_output is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Playable Scene not found")
    return playable_scene_output

@app.get("/chapters/{chapter_id}/playable-scenes")
def get_playable_scenes_by_chapter(chapter_id: str)->List[PlayableScene]:
    playable_scene_output=get_playable_scenes(chapter_id)
    # if not playable_scene_output:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Playable Scene not found")
    return playable_scene_output

@app.get("/playthroughs/{playthrough_id}/chapters/{chapter_id}/progress")
def get_playthrough_progress(playthrough_id: str,chapter_id:str)->SceneProgress:
    progress_output=get_scene_progress(playthrough_id,chapter_id)
    if progress_output is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Progress not found")
    return progress_output

@app.put("/playthroughs/{playthrough_id}/chapters/{chapter_id}/progress")
def update_scene_progress(playthrough_id: str, chapter_id: str,scene_progress:SceneProgress):
    if playthrough_id!=scene_progress.playthrough_id or chapter_id!=scene_progress.chapter_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Path Ids must match Body Ids")
    save_scene_progress(scene_progress)
    return scene_progress

@app.post("/chapters/{chapter_id}/playable-scenes/generate")
def generate_playable_scene_by_id(chapter_id:str,generation_request:SceneGenerationRequest)->PlayableScene:
    scene_bible_output=get_scene_bible(chapter_id)
    if scene_bible_output is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Scene Bible not found")
    scene_plan = generate_scene_plan(
        chapter_excerpt=generation_request.chapter_excerpt,
        scene_bible=scene_bible_output,
        position=generation_request.position,
        known_context=generation_request.chapter_excerpt,
        locked_clue_content=[],
    )
    playable_scene=build_playable_scene_from_plan(scene_plan)
    playable_scene.scene_id=f"{chapter_id}-scene-{generation_request.position}"
    save_playable_scene(playable_scene)
    return playable_scene

@app.post("/chapters/{chapter_id}/generate")
def generate_chapter_by_id(chapter_id: str) -> dict:
    try:
        return generate_playable_chapter(chapter_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))

