# Security Policy for RAG Chatbot

## Security Overview

This document outlines the security measures implemented in the RAG Chatbot API for the Physical AI & Humanoid Robotics book.

## Authentication & Authorization

### API Key Authentication
- All endpoints require API key authentication via the `X-API-Key` header
- Separate API keys are used for regular queries vs admin functions
- Invalid API keys return HTTP 401 Unauthorized

### Admin Endpoints
- Admin endpoints (`/admin/ingest`, `/admin/refresh`) require a separate admin API key
- Access is strictly limited to authorized personnel

## Input Validation

### Request Validation
- All input parameters are validated using Pydantic models
- Text inputs have minimum and maximum length restrictions
- Special characters are properly escaped to prevent injection attacks
- Query parameters are sanitized before processing

### Content Processing
- Book content is validated before ingestion
- Malicious content patterns are checked during processing
- File types are restricted to safe formats (Markdown, text)

## Data Protection

### Content Storage
- Book content is stored in Qdrant vector database
- Content is not stored in plain text in application memory beyond the session
- No user-specific data is retained beyond the session lifetime

### API Keys
- API keys are loaded from environment variables, not hardcoded
- API keys are not logged or exposed in responses
- Keys should be rotated periodically

## Rate Limiting

- Rate limiting is implemented to prevent abuse
- Default limit: 10 requests per minute per IP address
- Exceeding limits returns HTTP 429 Too Many Requests

## Logging & Monitoring

### Secure Logging
- API keys are not logged
- User queries are logged for debugging but not sensitive data
- Error logs do not expose system details to users

## Security Testing

### Performed Tests
- Input validation testing
- Authentication bypass attempts
- Rate limiting verification
- SQL injection and XSS prevention

## Deployment Security

### Environment
- Deploy in a secure environment with proper network isolation
- Use HTTPS in production
- Keep dependencies updated
- Regular security audits of dependencies

## Reporting Security Issues

If you discover a security vulnerability, please contact the maintainers directly. Do not report security issues in public forums or issue trackers.

## Security Best Practices for Users

1. Use strong, unique API keys
2. Rotate API keys regularly
3. Monitor API usage for unusual patterns
4. Use HTTPS when calling the API
5. Validate responses before displaying to users