from fastapi import FastAPI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import API routes
from api.health import router as health_router
from api.chatbot import router as query_router  # Renamed from chatbot_router since it now handles /query
from api.admin import router as admin_router

# Import configuration and error handling
from core.config import settings
from core.errors import register_error_handlers
from core.middleware import add_rate_limiting

app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    debug=settings.debug
)

# Register error handlers
app = register_error_handlers(app)

# Add rate limiting middleware
app = add_rate_limiting(app)

# Include API routes
app.include_router(health_router)
app.include_router(query_router)
app.include_router(admin_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)