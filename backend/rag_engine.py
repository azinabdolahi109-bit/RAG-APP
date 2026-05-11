import pandas as pd
import numpy as np
import os
import pickle
from sentence_transformers import SentenceTransformer
from typing import List, Dict

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    print("[WARNING] FAISS not found. Falling back to NumPy-based vector search.")
    FAISS_AVAILABLE = False

class RAGEngine:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.embeddings = None # For NumPy fallback
        self.chunks = []
        self.index_path = "data/faiss_index.bin"
        self.embeddings_path = "data/embeddings.pkl"
        self.chunks_path = "data/chunks.pkl"

    def index_excel(self, file_path: str):
        """Reads all sheets and converts rows into structured text chunks."""
        excel_data = pd.read_excel(file_path, sheet_name=None)
        self.chunks = []
        
        for sheet_name, df in excel_data.items():
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
        self.embeddings = np.array(embeddings).astype("float32")
        
        if FAISS_AVAILABLE:
            dimension = self.embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(self.embeddings)
            faiss.write_index(self.index, self.index_path)
        
        # Always save chunks and raw embeddings for fallback
        with open(self.chunks_path, "wb") as f:
            pickle.dump(self.chunks, f)
        with open(self.embeddings_path, "wb") as f:
            pickle.dump(self.embeddings, f)
            
        return True

    def load_index(self):
        """Loads index or embeddings from disk."""
        if not os.path.exists(self.chunks_path):
            return False

        with open(self.chunks_path, "rb") as f:
            self.chunks = pickle.load(f)
            
        if FAISS_AVAILABLE and os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            return True
        elif os.path.exists(self.embeddings_path):
            with open(self.embeddings_path, "rb") as f:
                self.embeddings = pickle.load(f)
            return True
            
        return False

    def retrieve(self, query: str, k=5) -> List[str]:
        """Retrieves top-k relevant chunks for a query."""
        if self.index is None and self.embeddings is None:
            if not self.load_index():
                return []
                
        query_embedding = self.model.encode([query]).astype("float32")
        
        if FAISS_AVAILABLE and self.index is not None:
            distances, indices = self.index.search(query_embedding, k)
            idx_list = indices[0]
        else:
            # Simple NumPy Cosine Similarity (Dot product on normalized vectors)
            # Or just L2 distance
            if self.embeddings is None: return []
            
            # Simple L2 distance fallback
            diff = self.embeddings - query_embedding
            dist = np.linalg.norm(diff, axis=1)
            idx_list = np.argsort(dist)[:k]
        
        results = []
        for idx in idx_list:
            if 0 <= idx < len(self.chunks):
                results.append(self.chunks[idx])
        return results
