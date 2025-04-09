from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from typing import List
# from .vector_store import VectorStore
from app.vector_store import VectorStore
import os


app = FastAPI()
vector_store = VectorStore()

class BatchRequest(BaseModel):
    querys: list
    k: int = 3

class SearchRequest(BaseModel):
    query: str
    k: int = 3

class DocumentResponse(BaseModel):
    content: str
    metadata: dict

@app.post("/search")
async def search(request: SearchRequest):
    results = vector_store.search(request.query, request.k)
    return {"results": [{"content": doc.page_content, "metadata": doc.metadata} for doc in results]}

@app.post("/batch_search")
async def search(request: BatchRequest):
    results = vector_store.batch_search(request.querys, request.k)
    return {"results": [{"content": doc.page_content, "metadata": doc.metadata} for doc in results]}

@app.post("/add-documents")
async def add_documents(files: List[UploadFile] = File(...)):
    saved_files = []
    for file in files:
        content = await file.read()
        with open(f"temp_{file.filename}", "wb") as f:
            f.write(content)
        saved_files.append(f"temp_{file.filename}")
    vector_store.add_documents(saved_files)
    for file_path in saved_files:
        if os.path.exists(file_path):
            os.remove(file_path)
    return {"message": "Documents added successfully", "count": vector_store.count()}