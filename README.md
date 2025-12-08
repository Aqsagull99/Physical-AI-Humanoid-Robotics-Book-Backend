# RAG Chatbot - Physical AI & Humanoid Robotics

## Overview
This RAG (Retrieval-Augmented Generation) chatbot provides an interactive Q&A interface for the Physical AI & Humanoid Robotics book. It uses OpenAI SDK for embeddings and responses, Qdrant for vector storage, and FastAPI for the backend API.

## Architecture
- **Frontend**: React-based ChatKit UI integrated with Docusaurus
- **Backend**: FastAPI application with endpoints for querying and ingestion
- **Vector Database**: Qdrant Cloud for storing document embeddings
- **LLM**: OpenAI SDK for generating responses based on retrieved content

## API Endpoints

### `/query` (POST)
Submit a question to the chatbot.

Request body:
```json
{
  "text": "Your question here",
  "selected_text": "Optional selected text to focus on",
  "top_k": 5
}
```

Response:
```json
{
  "text": "The chatbot's answer",
  "sources": [
    {
      "id": "source_id",
      "content": "Source content",
      "metadata": {
        "file_path": "source_file.md",
        "chunk_id": 0,
        "type": "paragraph"
      }
    }
  ]
}
```

### `/admin/ingest` (POST)
Ingest book content into the vector database.
- Requires admin API key in `X-API-Key` header
- Response: `{"status": "success", "message": "Content ingested successfully"}`

### `/health` (GET)
Check the health status of the service.
- Response: `{"status": "healthy", "timestamp": "...", "version": "1.0.0"}`

## Environment Variables
Create a `.env` file in the `rag-backend` directory:

```
OPENAI_API_KEY=your-openai-api-key
QDRANT_URL=your-qdrant-cloud-url
QDRANT_API_KEY=your-qdrant-api-key
API_KEY=your-secret-api-key
ADMIN_API_KEY=your-admin-api-key
BOOK_CONTENT_PATH=../Robotic Book/docs
```

## Setup and Installation

### Backend Setup
1. Navigate to the `rag-backend` directory:
   ```bash
   cd rag-backend
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables (see above)

4. Run the backend:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

### Frontend Setup
The frontend is integrated with the Docusaurus documentation site. No additional setup is required beyond the standard Docusaurus installation.

## Ingesting Content
Before using the chatbot, you need to ingest the book content:

1. Ensure your book content is available in the configured `BOOK_CONTENT_PATH`
2. Make a POST request to `/admin/ingest` with your admin API key:
   ```bash
   curl -X POST http://localhost:8000/admin/ingest \
     -H "X-API-Key: your-admin-api-key"
   ```

## Security
- API endpoints are protected with API keys
- Admin endpoints require a separate admin API key
- Input validation is implemented to prevent injection attacks
- Rate limiting is implemented to prevent abuse

## Performance
- Response times are monitored and logged
- Vector store operations are optimized
- Content is chunked by headers for efficient retrieval

## Troubleshooting
- Check logs for error messages
- Verify API keys are correctly configured
- Ensure Qdrant connection details are correct
- Confirm book content path is accessible