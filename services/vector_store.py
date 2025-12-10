import os
import pickle
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from core.logging import logger
from core.config import settings
from services.embedding_generator import get_embedding_generator

# Try to import Qdrant, fallback to local storage if not available
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.models import PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logger.warning("Qdrant client not installed. Install with: pip install qdrant-client")

class VectorStore:
    """
    Vector store to save and retrieve embeddings with Qdrant support
    """

    def __init__(self, storage_path: Optional[str] = None, collection_name: str = "robotics_book_content"):
        self.storage_path = storage_path or settings.vector_store_path
        self.collection_name = collection_name
        self.qdrant_client = None
        self.embeddings = []
        self.metadata = []
        self.ids = []

        # Initialize Qdrant if available and configured
        if QDRANT_AVAILABLE and settings.vector_store_type == "qdrant":
            try:
                if settings.qdrant_url and settings.qdrant_api_key:
                    self.qdrant_client = QdrantClient(
                        url=settings.qdrant_url,
                        api_key=settings.qdrant_api_key,
                        prefer_grpc=False,  # Using HTTP for better compatibility
                        timeout=300  # Increase timeout to 5 minutes for large operations
                    )
                elif settings.qdrant_url:
                    self.qdrant_client = QdrantClient(
                        url=settings.qdrant_url,
                        timeout=300  # Increase timeout to 5 minutes for large operations
                    )
                else:
                    # Local Qdrant instance
                    self.qdrant_client = QdrantClient(
                        path="./qdrant_data",
                        timeout=300  # Increase timeout to 5 minutes for large operations
                    )

                # Create collection if it doesn't exist
                self._create_collection_if_not_exists()
                logger.info(f"Qdrant client initialized with collection: {self.collection_name}")
            except Exception as e:
                logger.error(f"Error initializing Qdrant: {e}")
                logger.info("Falling back to local storage")
                self.qdrant_client = None
                self._ensure_storage_directory()
        else:
            # Use local storage
            self._ensure_storage_directory()

    def _ensure_storage_directory(self):
        """
        Ensure the storage directory exists
        """
        os.makedirs(self.storage_path, exist_ok=True)

    def _create_collection_if_not_exists(self):
        """
        Create Qdrant collection if it doesn't exist
        """
        try:
            collections = self.qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if self.collection_name not in collection_names:
                # Get embedding dimension from the embedding generator
                sample_embedding = get_embedding_generator().generate_embedding("sample text")
                vector_size = len(sample_embedding)

                # Create collection with specified vector size
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=vector_size,
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"Qdrant collection {self.collection_name} already exists")
        except Exception as e:
            logger.error(f"Error creating Qdrant collection: {e}")
            raise

    async def add_embeddings(self, embeddings: List[np.ndarray], metadata: List[Dict[str, Any]], ids: List[str]):
        """
        Add embeddings to the vector store (Qdrant or local)
        """
        logger.info(f"Adding {len(embeddings)} embeddings to vector store")

        if self.qdrant_client is not None:
            # Add to Qdrant
            points = []
            for i, (embedding, meta, point_id) in enumerate(zip(embeddings, metadata, ids)):
                points.append(PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload=meta
                ))

            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
        else:
            # Add to local storage
            self.embeddings.extend(embeddings)
            self.metadata.extend(metadata)
            self.ids.extend(ids)

    async def add_content(self, content_list: List[Dict[str, Any]]):
        """
        Add content to the vector store by generating embeddings
        """
        logger.info(f"Adding {len(content_list)} content items to vector store")

        texts = [item['content'] for item in content_list]
        embeddings = get_embedding_generator().generate_embeddings(texts)

        metadata_list = [item.get('metadata', {}) for item in content_list]
        ids = [item.get('id', f"content_{i}") for i, item in enumerate(content_list)]

        await self.add_embeddings(embeddings, metadata_list, ids)

    async def find_similar(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """
        Find similar embeddings to the query embedding (Qdrant or local)
        """
        if self.qdrant_client is not None:
            # Search in Qdrant
            try:
                # For newer Qdrant client versions - synchronous call
                results = self.qdrant_client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding.tolist(),
                    limit=top_k,
                    with_payload=True
                )
            except Exception as e:
                # Fallback for different Qdrant client versions or API
                try:
                    # Try the legacy search_points method
                    results = self.qdrant_client.search_points(
                        collection_name=self.collection_name,
                        query_vector=query_embedding.tolist(),
                        limit=top_k,
                        with_payload=True
                    )
                except Exception as e2:
                    # Try using scroll as a fallback (returns all records, not semantic search)
                    try:
                        # Get all points from the collection as a fallback
                        # The scroll method returns (records, next_page_offset)
                        scroll_result = self.qdrant_client.scroll(
                            collection_name=self.collection_name,
                            limit=top_k,  # limit to top_k results
                            with_payload=True
                        )

                        # Format scroll results to match search format
                        results = []
                        records, next_page_offset = scroll_result
                        for i in range(min(len(records), top_k)):
                            record = records[i]
                            # Create a mock result object - for scroll we don't have real scores
                            mock_result = type('MockResult', (), {
                                'id': record.id,
                                'payload': record.payload,
                                'score': 0.1  # low score since it's not a real semantic match
                            })()
                            results.append(mock_result)
                    except Exception as e3:
                        # If all methods fail, log error and return empty results
                        logger.error(f"Qdrant client does not have expected search methods. search error: {e}, search_points error: {e2}, scroll error: {e3}")
                        return []

                # Format results to match local storage format
                formatted_results = []
                for result in results:
                    # Ensure content is available from the payload
                    content = result.payload.get('content', result.payload.get('text', ''))
                    formatted_results.append((
                        {
                            'id': result.id,
                            'metadata': result.payload,
                            'content': content
                        },
                        result.score
                    ))
                return formatted_results
            except Exception as e:
                logger.error(f"Error searching in Qdrant: {e}")
                return []
        else:
            # Search in local storage
            if len(self.embeddings) == 0:
                return []

            # Calculate cosine similarity
            similarities = []
            for i, stored_embedding in enumerate(self.embeddings):
                # Cosine similarity: (A · B) / (||A|| * ||B||)
                dot_product = np.dot(query_embedding, stored_embedding)
                norm_product = np.linalg.norm(query_embedding) * np.linalg.norm(stored_embedding)

                if norm_product == 0:
                    similarity = 0
                else:
                    similarity = dot_product / norm_product

                similarities.append((i, similarity))

            # Sort by similarity (descending) and get top_k
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_similarities = similarities[:top_k]

            # Prepare results with metadata and similarity scores
            results = []
            for idx, similarity in top_similarities:
                result = {
                    'id': self.ids[idx],
                    'metadata': self.metadata[idx],
                    'content': self.metadata[idx].get('content', '')  # This might not be stored here
                }
                results.append((result, similarity))

            return results

    async def find_similar_texts(self, query: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """
        Find similar texts to the query string
        """
        query_embedding = get_embedding_generator().generate_embedding(query)
        return await self.find_similar(query_embedding, top_k)

    def save(self, filename: str = "vector_store.pkl"):
        """
        Save the vector store to disk (only for local storage)
        """
        if self.qdrant_client is not None:
            logger.info("Qdrant storage - no need to save locally")
            return

        filepath = os.path.join(self.storage_path, filename)
        logger.info(f"Saving vector store to {filepath}")

        data = {
            'embeddings': self.embeddings,
            'metadata': self.metadata,
            'ids': self.ids
        }

        with open(filepath, 'wb') as f:
            pickle.dump(data, f)

    def load(self, filename: str = "vector_store.pkl"):
        """
        Load the vector store from disk (only for local storage)
        """
        if self.qdrant_client is not None:
            logger.info("Qdrant storage - loading handled by Qdrant service")
            return

        filepath = os.path.join(self.storage_path, filename)
        if not os.path.exists(filepath):
            logger.warning(f"Vector store file {filepath} does not exist, initializing empty store")
            return

        logger.info(f"Loading vector store from {filepath}")

        with open(filepath, 'rb') as f:
            data = pickle.load(f)

        self.embeddings = data['embeddings']
        self.metadata = data['metadata']
        self.ids = data['ids']

    def clear(self):
        """
        Clear all embeddings from the vector store
        """
        if self.qdrant_client is not None:
            # Clear Qdrant collection
            try:
                self.qdrant_client.delete_collection(self.collection_name)
                self._create_collection_if_not_exists()  # Recreate empty collection
                logger.info(f"Cleared Qdrant collection: {self.collection_name}")
            except Exception as e:
                logger.error(f"Error clearing Qdrant collection: {e}")
        else:
            # Clear local storage
            logger.info("Clearing vector store")
            self.embeddings = []
            self.metadata = []
            self.ids = []

# Lazy singleton instance
_vector_store_instance = None

def get_vector_store():
    """
    Get the vector store instance, creating it if it doesn't exist
    """
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance