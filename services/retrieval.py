from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from core.logging import logger
from core.performance import monitor_performance
from services.content_loader import get_content_loader
from services.embedding_generator import get_embedding_generator
from services.vector_store import get_vector_store

class RetrievalService:
    """
    Service to handle RAG retrieval logic - find relevant content based on user queries
    """

    def __init__(self):
        self.content_loader = None
        self.vector_store = None

    @monitor_performance
    async def initialize_store(self):
        """
        Initialize the vector store with book content
        """
        logger.info("Initializing vector store with book content")

        # Load content from the book using lazy service
        content = get_content_loader().load_content()

        # Add content to vector store using lazy service
        await get_vector_store().add_content(content)

        # Save the vector store using lazy service
        get_vector_store().save()

        logger.info(f"Vector store initialized with {len(content)} content chunks")

    @monitor_performance
    async def retrieve_relevant_content(self, query: str, top_k: int = 5, selected_text: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant content based on the query
        If selected_text is provided, only search within that text
        """
        logger.info(f"Retrieving relevant content for query: {query[:50]}...")

        if selected_text:
            # If specific text is selected, only search within that text
            return await self._retrieve_from_selected_text(query, selected_text, top_k)
        else:
            # Search in the full vector store
            return await self._retrieve_from_full_store(query, top_k)

    async def _retrieve_from_selected_text(self, query: str, selected_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant content from the selected text only
        In selection-only mode, we focus the search on the selected text
        """
        logger.info("Performing retrieval from selected text only")

        # Generate embedding for the query
        query_embedding = get_embedding_generator().generate_embedding(query)

        # Generate embedding for the selected text
        selected_embedding = get_embedding_generator().generate_embedding(selected_text)

        # Calculate similarity between query and selected text
        # Cosine similarity
        dot_product = np.dot(query_embedding, selected_embedding)
        norm_product = np.linalg.norm(query_embedding) * np.linalg.norm(selected_embedding)

        if norm_product == 0:
            similarity = 0
        else:
            similarity = dot_product / norm_product

        # Create result with the selected text and similarity score
        # Ensure all required fields are included in metadata
        result = {
            'id': 'selected_text',
            'content': selected_text,
            'metadata': {
                'file_path': 'selected_text',
                'chunk_id': 0,
                'section': 'Selected Text',
                'source': 'selected_text',
                'type': 'selection',
                'relevance': similarity
            },
            'similarity': float(similarity)
        }

        return [result]

    async def _retrieve_from_full_store(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant content from the full vector store
        """
        logger.info(f"Performing retrieval from full store, top_k: {top_k}")

        # Load vector store if it hasn't been loaded yet using lazy service
        get_vector_store().load()

        # Find similar content using lazy service
        results = await get_vector_store().find_similar_texts(query, top_k)

        # Format results
        formatted_results = []
        for content_item, similarity in results:
            formatted_result = {
                'id': content_item['id'],
                'content': content_item.get('content', ''),
                'metadata': content_item['metadata'],
                'similarity': float(similarity)
            }
            formatted_results.append(formatted_result)

        logger.info(f"Retrieved {len(formatted_results)} relevant content items")
        return formatted_results

    def get_sources_for_content(self, content_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract and format source information from content metadata
        """
        sources = []
        for item in content_list:
            metadata = item.get('metadata', {})
            source_info = {
                'id': item.get('id'),
                'source_file': metadata.get('file_path', 'unknown'),
                'chunk_index': metadata.get('chunk_id', -1),
                'type': metadata.get('type', 'unknown'),
                'similarity': item.get('similarity', 0.0)
            }
            sources.append(source_info)

        return sources

# Lazy singleton instance
_retrieval_service_instance = None

def get_retrieval_service():
    """
    Get the retrieval service instance, creating it if it doesn't exist
    """
    global _retrieval_service_instance
    if _retrieval_service_instance is None:
        _retrieval_service_instance = RetrievalService()
    return _retrieval_service_instance
