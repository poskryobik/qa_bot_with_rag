from pydantic import BaseModel

class LLMRequest(BaseModel):
    query: str

class QuestionRequest(BaseModel):
    text: str

class GenerationResponse(BaseModel):
    response: str

class DocumentResponse(BaseModel):
    content: str
    metadata: dict

class SearchRequest(BaseModel):
    query: str
    k: int = 3