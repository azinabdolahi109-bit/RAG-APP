import pandas as pd
import faiss
import numpy as np
import os
import pickle
from sentence_transformers import SentenceTransformer
from typing import List, Dict

class RAGEngine:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.chunks = []
        self.index_path = "data/faiss_index.bin"
        self.chunks_path = "data/chunks.pkl"

    def process_excel(self, file_path: str):
        """Reads all sheets and converts rows into structured text chunks."""
        excel_data = pd.read_excel(file_path, sheet_name=None)
        self.chunks = []
        
        for sheet_name, df in excel_data.items():
            # Convert NaN to empty string for cleaner text
            df = df.fillna("")
            headers = df.columns.tolist()
            
            for idx, row in df.iterrows():
                row_str = ", ".join([f"{headers[i]}: {row[headers[i]]}" for i in range(len(headers))])
                chunk = f"Sheet: {sheet_name} | Row: {idx + 1} | Content: {row_str}"
                self.chunks.append(chunk)
        
        if not self.chunks:
            return False
            
        # Generate embeddings
        embeddings = self.model.encode(self.chunks)
        
        # Build FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(embeddings).astype("float32"))
        
        # Persist locally
        self.save_index()
        return True

    def save_index(self):
        """Saves the FAISS index and chunks to disk."""
        if self.index is not None:
            faiss.write_index(self.index, self.index_path)
            with open(self.chunks_path, "wb") as f:
                pickle.dump(self.chunks, f)

    def load_index(self):
        """Loads the FAISS index and chunks from disk."""
        if os.path.exists(self.index_path) and os.path.exists(self.chunks_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.chunks_path, "rb") as f:
                self.chunks = pickle.load(f)
            return True
        return False

    def retrieve(self, query: str, k=5) -> List[str]:
        """Retrieves top-k relevant chunks for a query."""
        if self.index is None:
            # Try loading if not in memory
            if not self.load_index():
                return []
                
        query_embedding = self.model.encode([query])
        distances, indices = self.index.search(np.array(query_embedding).astype("float32"), k)
        
        results = []
        for idx in indices[0]:
            if idx < len(self.chunks):
                results.append(self.chunks[idx])
        return results
