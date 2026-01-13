import faiss
import numpy as np
import google.genai as genai
from google.genai import types
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import threading
from pathlib import Path
import pickle

from app.utils.logget_setup import ai_logger as logger
from app.core.configs.app_config import settings, INDEX_STORAGE_DIR


client = genai.Client(api_key=settings.GOOGLE_API_KEY)

class GeminiSearchEngineError(Exception):
    """Base exception for GeminiSearchEngine"""
    pass


class EmbeddingError(GeminiSearchEngineError):
    """Raised when embedding generation fails"""
    pass


class DocumentNotFoundError(GeminiSearchEngineError):
    """Raised when document lookup fails"""
    pass


class GeminiSearchEngine:
    """
    Production-grade semantic search engine using FAISS and Gemini embeddings.
    
    This class mimics Azure AI Search functionality by combining:
    - Vector Index (FAISS) for similarity search
    - Document Store for metadata and content retrieval
    """
    
    def __init__(
        self, 
        dimension: int = 3072,
        index_type: str = "flat",
        max_retries: int = 3
    ):
        """
        Initialize the search engine.
        
        Args:
            client: Authenticated Google GenAI client
            dimension: Embedding dimension (must match model output)
            index_type: FAISS index type ("flat" or "ivf")
            max_retries: Maximum retry attempts for API calls
            
        Raises:
            ValueError: If invalid parameters provided
        """
        
        if dimension <= 0:
            raise ValueError(f"Dimension must be positive, got {dimension}")
        if max_retries < 1:
            raise ValueError(f"max_retries must be >= 1, got {max_retries}")
            
        self.client: genai.Client = client
        self.dimension = dimension
        self.max_retries = max_retries
        self._lock = threading.Lock()  # Thread safety for index operations
        
        # Initialize FAISS index based on type
        if index_type == "flat":
            self.index = faiss.IndexFlatL2(dimension)
        elif index_type == "ivf":
            # IVF index for larger datasets (requires training)
            quantizer = faiss.IndexFlatL2(dimension)
            self.index = faiss.IndexIVFFlat(quantizer, dimension, 100)
        else:
            raise ValueError(f"Unknown index_type: {index_type}")
            
        self.doc_store: Dict[int, Dict[str, Any]] = {}
        self._is_trained = (index_type == "flat")  # Flat index doesn't need training
        
        logger.debug(f"Initialized GeminiSearchEngine with dimension={dimension}, index_type={index_type}")

    def _embed_text(
        self, 
        text: str, 
        task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> np.ndarray:
        """
        Generate embedding for text with retry logic.
        
        Args:
            text: Text to embed
            task_type: "RETRIEVAL_DOCUMENT" or "RETRIEVAL_QUERY"
            
        Returns:
            Embedding vector as numpy array
            
        Raises:
            EmbeddingError: If embedding generation fails after retries
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
            
        for attempt in range(self.max_retries):
            try:
                result = self.client.models.embed_content(
                    model="models/gemini-embedding-001",
                    contents=text,
                    config=types.EmbedContentConfig(
                        task_type=task_type,
                        output_dimensionality=self.dimension
                    )
                )
                
                if not result or not result.embeddings:
                    raise EmbeddingError
                
                vector = np.array(
                    result.embeddings[0].values, #type: ignore
                    dtype='float32'
                ).reshape(1, -1)
                
                # Validate embedding dimension
                if vector.shape[1] != self.dimension:
                    raise EmbeddingError(
                        f"Expected dimension {self.dimension}, got {vector.shape[1]}"
                    )
                    
                return vector
                
            except Exception as e:
                logger.warning(
                    f"Embedding attempt {attempt + 1}/{self.max_retries} failed: {e}"
                )
                if attempt == self.max_retries - 1:
                    raise EmbeddingError(
                        f"Failed to generate embedding after {self.max_retries} attempts"
                    ) from e
                    
        raise EmbeddingError("Unexpected error in embedding generation")

    def upload_document(self, doc_id: str, searchable_text: str) -> int:
        """
        Upload and index a document.
        
        Args:
            doc_id: Unique document identifier
            searchable_text: Text content to index
            
        Returns:
            Internal FAISS index ID
            
        Raises:
            ValueError: If inputs are invalid
            EmbeddingError: If embedding generation fails
        """
        if not doc_id:
            raise ValueError("doc_id cannot be empty")
        if not searchable_text or not searchable_text.strip():
            raise ValueError("searchable_text cannot be empty")
            
        logger.debug(f"Uploading document: {doc_id}")
        
        try:
            # Generate embedding
            vector = self._embed_text(searchable_text, task_type="RETRIEVAL_DOCUMENT")
            
            # Thread-safe index update
            with self._lock:
                faiss_id = self.index.ntotal
                self.index.add(vector) #type: ignore
                
                # Store document metadata
                self.doc_store[faiss_id] = {
                    "id": doc_id,
                    "content": searchable_text
                }
                
            logger.debug(f"Document {doc_id} indexed successfully with internal ID {faiss_id}")
            return faiss_id
            
        except Exception as e:
            logger.error(f"Failed to upload document {doc_id}: {e}")
            raise

    def search(
        self, 
        query_text: str, 
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query_text: Search query
            top_k: Number of results to return
            
        Returns:
            List of search results with score, id, and document
            
        Raises:
            ValueError: If inputs are invalid
            EmbeddingError: If query embedding fails
            RuntimeError: If index is empty
        """
        if not query_text or not query_text.strip():
            raise ValueError("query_text cannot be empty")
        if top_k <= 0:
            raise ValueError(f"top_k must be positive, got {top_k}")
            
        if self.index.ntotal == 0:
            logger.warning("Search called on empty index")
            return []
            
        logger.debug(f"Searching for: '{query_text[:50]}...' (top_k={top_k})")
        
        try:
            # Generate query embedding
            query_vec = self._embed_text(query_text, task_type="RETRIEVAL_QUERY")
            
            # Search FAISS index
            with self._lock:
                distances, indices = self.index.search(query_vec, k=top_k) #type: ignore
            
            # Format results
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx != -1 and idx in self.doc_store:
                    doc = self.doc_store[idx]
                    results.append({
                        "score": float(dist),
                        "id": doc["id"],
                        "document": doc["content"]
                    })
                elif idx != -1:
                    logger.warning(f"Index {idx} not found in doc_store")
                    
            logger.debug(f"Search returned {len(results)} results")
            return results
            
        except EmbeddingError:
            raise
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise RuntimeError(f"Search operation failed: {e}") from e

    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve document by its ID.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            Document data or None if not found
        """
        with self._lock:
            for doc_data in self.doc_store.values():
                if doc_data["id"] == doc_id:
                    return doc_data
        return None

    def delete_document(self, doc_id: str) -> bool:
        """
        Delete document from the store (marks as deleted, FAISS doesn't support removal).
        
        Args:
            doc_id: Document identifier
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            for faiss_id, doc_data in list(self.doc_store.items()):
                if doc_data["id"] == doc_id:
                    del self.doc_store[faiss_id]
                    logger.debug(f"Deleted document: {doc_id}")
                    return True
        logger.warning(f"Document not found for deletion: {doc_id}")
        return False

    def save(self) -> None:
        """
        Persist index and document store to disk.
        
        Args:
            directory: Directory path to save files
        """
        directory = INDEX_STORAGE_DIR
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        
        with self._lock:
            # Save FAISS index
            index_path = dir_path / "faiss.index"
            faiss.write_index(self.index, str(index_path))
            
            # Save document store
            store_path = dir_path / "doc_store.pkl"
            with open(store_path, 'wb') as f:
                pickle.dump(self.doc_store, f)
                
        logger.debug(f"Index saved to {directory}")

    def load(self) -> bool:
        """
        Populates the current instance with data from disk.
        Returns True if successful, False if files don't exist.
        """
        directory = INDEX_STORAGE_DIR
        dir_path = Path(directory)
        index_path = dir_path / "faiss.index"
        store_path = dir_path / "doc_store.pkl"

        if not index_path.exists() or not store_path.exists():
            logger.warning(f"No index files found in {directory}")
            return False

        with self._lock:
            # Load FAISS
            self.index = faiss.read_index(str(index_path))
            
            # Load Document Store
            with open(store_path, 'rb') as f:
                self.doc_store = pickle.load(f)
                
        logger.info(f"Index loaded. Total documents: {len(self)}")
        return True

    def get_stats(self) -> Dict[str, Any]:
        """
        Get index statistics.
        
        Returns:
            Dictionary with index statistics
        """
        with self._lock:
            return {
                "total_documents": self.index.ntotal,
                "dimension": self.dimension,
                "doc_store_size": len(self.doc_store)
            }

    def __len__(self) -> int:
        """Return number of indexed documents"""
        return self.index.ntotal

    def __repr__(self) -> str:
        return f"GeminiSearchEngine(documents={len(self)}, dimension={self.dimension})"
    

gemini_search_engine = GeminiSearchEngine()