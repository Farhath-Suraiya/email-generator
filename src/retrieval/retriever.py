import os
from typing import List, Dict, Any
from src.retrieval.index import FAISSIndexManager, INDEX_DIR
from src.retrieval.embeddings import DEFAULT_MODEL_NAME

class EmailRetriever:
    def __init__(self, index_dir: str = INDEX_DIR, model_name: str = DEFAULT_MODEL_NAME):
        self.index_manager = FAISSIndexManager(index_dir=index_dir, model_name=model_name)
        if not self.index_manager.index_file.exists():
            # Build index if not existing
            self.index_manager.build_index()
        else:
            self.index_manager.load_index()

    def retrieve_similar_emails(self, email: str, top_k: int = 3) -> List[Dict[str, Any]]:
        if not email or not email.strip():
            return []

        query_embedding = self.index_manager.embedding_generator.encode(email, normalize=True)
        
        # FAISS search
        scores, indices = self.index_manager.index.search(query_embedding, top_k)
        
        results = []
        scores_flat = scores[0]
        indices_flat = indices[0]

        for score, idx in zip(scores_flat, indices_flat):
            if idx < 0 or idx >= len(self.index_manager.metadata):
                continue
            item = dict(self.index_manager.metadata[idx])
            item["score"] = float(score)
            results.append(item)

        return results

# Convenience standalone function interface
def retrieve_similar_emails(
    email: str,
    top_k: int = 3,
    index_dir: str = INDEX_DIR,
    model_name: str = DEFAULT_MODEL_NAME
) -> List[Dict[str, Any]]:
    retriever = EmailRetriever(index_dir=index_dir, model_name=model_name)
    return retriever.retrieve_similar_emails(email=email, top_k=top_k)
