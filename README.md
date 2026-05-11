# Excel RAG Assistant

A basic Retrieval-Augmented Generation (RAG) application that allows users to upload Excel files and ask questions about their content using Groq LLM and FAISS vector database.

## Tech Stack
- **Backend**: FastAPI, Pandas, FAISS, Sentence Transformers (all-MiniLM-L6-v2)
- **LLM**: Groq (Llama 3 8B)
- **Frontend**: React + Vite, Axios, Lucide React
- **Styling**: Vanilla CSS (Premium Dark Theme)

## Prerequisites
- Python 3.9+
- Node.js & npm
- [Groq API Key](https://console.groq.com/keys)

## Setup Instructions

### 1. Backend Setup
1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file (copy from `.env.example`) and add your Groq API key:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```
4. Run the FastAPI server:
   ```bash
   python main.py
   ```
   The backend will start at `http://localhost:8000`.

### 2. Frontend Setup
1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
   The frontend will start at `http://localhost:5173`.

## Functional Flow
1. **Upload**: User uploads an Excel file (.xlsx/.xls).
2. **Process**: Backend reads all sheets, chunks the rows, generates embeddings, and saves them to a local FAISS index.
3. **Ask**: User submits a question.
4. **Retrieve**: The system finds the most relevant rows in the Excel data.
5. **Answer**: Groq LLM generates an answer based on the retrieved context.

## Notes
- The FAISS index is persisted locally in the `backend/data/` directory.
- The app uses `llama3-8b-8192` on Groq for fast and accurate responses.
- All Excel sheets are automatically processed.
