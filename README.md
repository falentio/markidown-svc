# markidown-svc

A FastAPI service that converts various document formats to Markdown using Microsoft's MarkItDown library.

## Features

- Convert documents to Markdown format
- Supports multiple file formats (PDF, DOCX, XLSX, PPTX, images, HTML, etc.)
- RESTful API with FastAPI
- File size limit: 30MB
- API key authentication support
- Docker support

## Configuration

### Environment Variables

- `APIKEY` (optional): Comma-separated list of valid API keys for authentication
  - Example: `APIKEY=key1,key2,key3`
  - If not set or empty, API key validation is disabled
  - Copy `.env.example` to `.env` and configure your API keys

## Endpoints

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

### POST /transform
Transform uploaded file to Markdown.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Headers:
  - `X-Apikey`: API key for authentication (required if APIKEY environment variable is set)
- Body: file (form field)

**Response:**
```json
{
  "markdown": "# Converted markdown content...",
  "title": "Optional document title"
}
```

**Error Codes:**
- 401: Invalid or missing API key
- 413: File size exceeds 30MB limit
- 415: Unsupported file format
- 422: File conversion failed
- 500: Internal server error

## Running Locally

### Using uv

```bash
# Install dependencies
uv sync

# Configure environment variables (optional)
cp .env.example .env
# Edit .env and set your API keys

# Run the server
uv run uvicorn markidown_svc:app --reload
```

The API will be available at `http://localhost:8000`

### Using Docker

```bash
# Build the image
docker build -t markidown-svc:latest .

# Run the container (with API keys)
docker run -p 8000:8000 -e APIKEY=key1,key2,key3 markidown-svc:latest

# Or run without API key validation
docker run -p 8000:8000 markidown-svc:latest
```

## Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test transform endpoint (without API key if validation is disabled)
curl -X POST http://localhost:8000/transform \
  -F "file=@/path/to/your/document.pdf"

# Test transform endpoint (with API key)
curl -X POST http://localhost:8000/transform \
  -H "X-Apikey: your-api-key-here" \
  -F "file=@/path/to/your/document.pdf"
```

## License

See LICENSE file for details.
