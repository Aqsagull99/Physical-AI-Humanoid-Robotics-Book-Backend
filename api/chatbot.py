from fastapi import APIRouter, HTTPException, Depends
from core.auth import verify_api_key
from pydantic import BaseModel, Field
from pydantic.functional_validators import field_validator
from typing import List, Dict, Any, Optional
import openai
from core.logging import logger
from core.config import settings
from services.retrieval import get_retrieval_service
from services.content_loader import get_content_loader

router = APIRouter()

# Request and Response models
class QueryRequest(BaseModel):
    text: str  # Changed from 'query' to 'text' to match the OpenAPI spec
    selected_text: Optional[str] = None
    conversation_history: Optional[List[Dict[str, str]]] = None
    top_k: Optional[int] = Field(default=5, ge=1, le=20)  # Add validation: between 1 and 20

    @field_validator('text')
    @classmethod
    def text_must_not_be_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Text cannot be empty')
        if len(v) > 10000:  # Limit text length to prevent abuse
            raise ValueError('Text is too long (max 10000 characters)')
        return v

    @field_validator('selected_text')
    @classmethod
    def selected_text_must_not_be_empty(cls, v):
        if v is not None and (not v or len(v.strip()) == 0):
            raise ValueError('Selected text cannot be empty')
        if v is not None and len(v) > 10000:  # Limit text length to prevent abuse
            raise ValueError('Selected text is too long (max 10000 characters)')
        return v

class SourceReference(BaseModel):
    id: str
    content: str  # From OpenAPI spec
    metadata: Dict[str, Any]  # From OpenAPI spec

class QueryResponse(BaseModel):
    text: str  # Changed from 'response' to 'text' to match the OpenAPI spec
    sources: List[SourceReference]

@router.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest, api_key_valid: bool = Depends(verify_api_key)):
    """
    Query endpoint to handle user questions based on book content
    """
    logger.info(f"Received query request: {request.text[:50]}...")

    try:
        # Retrieve relevant content based on the query
        relevant_content = await get_retrieval_service().retrieve_relevant_content(
            query=request.text,  # Changed from request.query to request.text
            top_k=request.top_k,
            selected_text=request.selected_text
        )

        if not relevant_content:
            # Handle case where no relevant content is found in the book
            response_text = "I couldn't find any relevant content in the book to answer your question."
            sources = []
        else:
            # Generate response based on retrieved content from the book
            response_text = generate_response_from_content(
                request.text,  # Changed from request.query to request.text
                relevant_content,
                request.conversation_history
            )

            # Get source references
            sources = []
            for content_item in relevant_content:
                source_ref = SourceReference(
                    id=content_item.get('id', ''),
                    content=content_item.get('content', ''),
                    metadata=content_item.get('metadata', {})
                )
                sources.append(source_ref)

        logger.info(f"Generated response with {len(sources)} sources")

        return QueryResponse(
            text=response_text,  # Changed from response=response_text to text=response_text
            sources=sources
        )
    except Exception as e:
        logger.error(f"Error in query endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

def generate_response_from_content(query: str, content_list: List[Dict[str, Any]], conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
    """
    Generate a response based on the retrieved content from the book
    """
    # Combine the content for context
    context_text = "\n\n".join([item['content'] for item in content_list if item['content'].strip()])

    # If we have conversation history, include it
    history_context = ""
    if conversation_history:
        for msg in conversation_history[-3:]:  # Use last 3 exchanges
            history_context += f"User: {msg.get('user', '')}\nAssistant: {msg.get('assistant', '')}\n\n"

    # Construct the prompt for response generation that emphasizes using only book content
    prompt = f"""
    You are an expert assistant for the Physical AI & Humanoid Robotics book.
    Answer the user's question based ONLY on the following context from the book:

    Context:
    {context_text}

    Conversation History:
    {history_context}

    User Question: {query}

    Please provide a helpful and accurate answer based ONLY on the book content provided in the context. Do not use any external knowledge or general information. If the context doesn't contain enough information to answer the question, clearly state that the information is not available in the book.
    """

    # Return a response based on the book content
    if context_text.strip():
        response = f"Based on the book content:\n\n{context_text[:1000]}"
    else:
        response = "I couldn't find the relevant information in the book to answer your question."

    return response