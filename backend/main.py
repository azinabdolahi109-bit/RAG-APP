import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq
import logging
from rag_engine import RAGEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
logger.info(f"Loading .env from: {dotenv_path}")
load_dotenv(dotenv_path=dotenv_path)

app = FastAPI(title="Excel RAG API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG Engine
rag_engine = RAGEngine()

# Initialize Groq Client
groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key or groq_api_key == "YOUR_GROQ_API_KEY":
    logger.error("GROQ_API_KEY is missing or using placeholder in .env")
else:
    prefix = groq_api_key[:7] if len(groq_api_key) > 7 else "???"
    logger.info(f"GROQ_API_KEY detected: {prefix}...")

client = Groq(api_key=groq_api_key) if groq_api_key else None

if client:
    try:
        logger.info("Testing Groq connection...")
        client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1
        )
        logger.info("Groq API connection verified.")
    except Exception as e:
        logger.error(f"Groq connection test failed: {str(e)}")
else:
    logger.error("Groq client not initialized - no API key.")

class QuestionRequest(BaseModel):
    question: str

@app.get("/health")
async def health():
    return {"status": "healthy", "index_ready": rag_engine.index is not None}

@app.post("/upload")
async def upload_excel(file: UploadFile = File(...)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an Excel file.")
    
    # Save temporary file
    temp_path = f"data/{file.filename}"
    os.makedirs("data", exist_ok=True)
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        success = rag_engine.process_excel(temp_path)
        if not success:
            raise HTTPException(status_code=400, detail="Excel file is empty or could not be processed.")
        return {"message": "File uploaded and indexed successfully", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    if not client:
        raise HTTPException(status_code=500, detail="Groq client not initialized. Check GROQ_API_KEY.")
        
    if rag_engine.index is None:
        # Try to load if exists
        if not rag_engine.load_index():
            raise HTTPException(status_code=400, detail="No index found. Please upload a file first.")

    # Retrieve context
    context_chunks = rag_engine.retrieve(request.question)
    context_text = "\n".join(context_chunks)
    
    if not context_text:
        raise HTTPException(status_code=404, detail="No relevant context found in the uploaded data.")

    # Prepare prompt
    prompt = f"""
    You are a helpful assistant that answers questions based ONLY on the provided Excel data context.
    If the answer is not in the context, say you don't know based on the provided data.
    
    Context:
    {context_text}
    
    Question: {request.question}
    
    Answer:
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a data analyst assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
        )
        return {
            "answer": completion.choices[0].message.content,
            "sources": context_chunks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Groq API Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
