import json
import os
from pathlib import Path
from typing import List, Dict, Any
import faiss
import numpy as np

from src.retrieval.embeddings import EmbeddingGenerator, DEFAULT_MODEL_NAME

INDEX_DIR = os.getenv("VECTOR_DB_INDEX_PATH", "data/index")

class FAISSIndexManager:
    def __init__(self, index_dir: str = INDEX_DIR, model_name: str = DEFAULT_MODEL_NAME):
        self.index_dir = Path(index_dir)
        self.index_file = self.index_dir / "faiss_index.bin"
        self.metadata_file = self.index_dir / "metadata.json"
        self.embedding_generator = EmbeddingGenerator(model_name=model_name)
        self.index = None
        self.metadata: List[Dict[str, Any]] = []

    def build_index(self, train_path: str = "data/processed/train.json") -> int:
        train_file = Path(train_path)
        if not train_file.exists():
            raise FileNotFoundError(f"Training dataset not found at {train_path}")

        with open(train_file, "r", encoding="utf-8") as f:
            records = json.load(f)

        if not records:
            raise ValueError("Training dataset is empty.")

        incoming_emails = [r["incoming_email"] for r in records]
        
        # Save metadata mapping
        self.metadata = [
            {
                "id": r["id"],
                "category": r["category"],
                "incoming_email": r["incoming_email"],
                "reference_reply": r["reference_reply"]
            }
            for r in records
        ]

        # Generate normalized embeddings
        embeddings = self.embedding_generator.encode(incoming_emails, normalize=True)
        dimension = embeddings.shape[1]

        # Use Inner Product index (equivalent to Cosine Similarity for normalized vectors)
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings)

        self.save_index()
        return self.index.ntotal

    def save_index(self):
        self.index_dir.mkdir(parents=True, exist_ok=True)
        if self.index is not None:
            faiss.write_index(self.index, str(self.index_file))
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)

    def load_index(self):
        if not self.index_file.exists() or not self.metadata_file.exists():
            raise FileNotFoundError(f"Index or metadata missing in {self.index_dir}")

        self.index = faiss.read_index(str(self.index_file))
        with open(self.metadata_file, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

def build_and_save_index(train_path: str = "data/processed/train.json", index_dir: str = INDEX_DIR):
    manager = FAISSIndexManager(index_dir=index_dir)
    count = manager.build_index(train_path=train_path)
    print(f"Successfully built and persisted FAISS index with {count} vectors in {index_dir}")
    return manager

if __name__ == "__main__":
    build_and_save_index()
