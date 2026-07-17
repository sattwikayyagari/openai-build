from fastapi import FastAPI, UploadFile, HTTPException, status
from contextlib import asynccontextmanager
from uuid import uuid4
from database import init_db, save_book, get_book_details
from datetime import timezone, datetime

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    
app = FastAPI(lifespan=lifespan)



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