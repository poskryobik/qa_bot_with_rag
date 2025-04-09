from app.schemas import LLMRequest, QuestionRequest
from app.llm_client import LLMClient
from fastapi import FastAPI


app = FastAPI()
llm_client = LLMClient()

@app.post("/generate")
async def generate_direct(request: LLMRequest):
    response = llm_client.generate(query=request.query)
    return {"response": response}