from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # API Configuration
    api_title: str = "Physical AI & Humanoid Robotics Chatbot API"
    api_description: str = "API for the Physical AI & Humanoid Robotics book RAG chatbot"
    api_version: str = "1.0.0"

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # API Key Configuration
    api_key: Optional[str] = os.getenv("API_KEY")
    admin_api_key: Optional[str] = os.getenv("ADMIN_API_KEY")

    # Model Configuration
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"  # For backward compatibility
    llm_model: str = os.getenv("LLM_MODEL", "gemini/gemini-pro")  # Default to Gemini

    # Content Configuration
    book_content_path: str = os.getenv("BOOK_CONTENT_PATH", "../Robotic Book/docs")  # Point to docs directory
    embeddings_path: str = os.getenv("EMBEDDINGS_PATH", "./embeddings")

    # Vector Store Configuration
    vector_store_type: str = "qdrant"  # Options: "qdrant", "faiss", "chroma"
    vector_store_path: str = os.getenv("VECTOR_STORE_PATH", "./vector_store")  # Path for local vector store
    qdrant_url: Optional[str] = os.getenv("QDRANT_URL")
    qdrant_api_key: Optional[str] = os.getenv("QDRANT_API_KEY")

    # Retrieval Configuration
    default_top_k: int = 5
    max_top_k: int = 20
    min_similarity_threshold: float = 0.1

    # Rate Limiting
    max_concurrent_users: int = 100
    rate_limit_requests: int = 10  # requests per minute per user
    rate_limit_window: int = 60  # seconds

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


# Create a global settings instance
settings = Settings()