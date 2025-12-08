from typing import List, Dict, Any, Optional
import numpy as np
from core.logging import logger
from core.config import settings

class EmbeddingGenerator:
    """
    Service to generate embeddings for book content
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.embedding_model_name
        self.model = None
        self._load_model()

    def _load_model(self):
        """
        Load the embedding model
        """
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully")
        except ImportError:
            logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
            # Fallback to a simple mock implementation for testing
            self.model = None
        except Exception as e:
            logger.error(f"Error loading embedding model: {str(e)}")
            self.model = None

    def generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for a list of texts
        """
        if self.model is None:
            # Mock implementation for testing
            logger.warning("Using mock embeddings - install sentence-transformers for real embeddings")
            return [np.random.rand(384).astype(np.float32) for _ in texts]

        logger.info(f"Generating embeddings for {len(texts)} texts")
        embeddings = self.model.encode(texts)
        return [embedding.astype(np.float32) for embedding in embeddings]

    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text
        """
        return self.generate_embeddings([text])[0]

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embeddings
        """
        if self.model is None:
            return 384  # Default dimension for the mock model
        # Get the dimension by encoding a sample text
        sample_embedding = self.generate_embedding("sample text")
        return len(sample_embedding)

# Singleton instance
embedding_generator = EmbeddingGenerator()
