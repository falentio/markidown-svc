# markidown-svc

A FastAPI service that converts various document formats to Markdown using Microsoft's MarkItDown library.

## Features

- Convert documents to Markdown format
- Supports multiple file formats (PDF, DOCX, XLSX, PPTX, images, HTML, etc.)
- RESTful API with FastAPI
- File size limit: 30MB
- Docker support

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
- Body: file (form field)

**Response:**
```json
{
  "markdown": "# Converted markdown content...",
  "title": "Optional document title"
}
```

**Error Codes:**
- 413: File size exceeds 30MB limit
- 415: Unsupported file format
- 422: File conversion failed
- 500: Internal server error

## Running Locally

### Using uv

```bash
# Install dependencies
uv sync

# Run the server
uv run uvicorn markidown_svc:app --reload
```

The API will be available at `http://localhost:8000`

### Using Docker

```bash
# Build the image
docker build -t markidown-svc:latest .

# Run the container
docker run -p 8000:8000 markidown-svc:latest
```

## Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test transform endpoint
curl -X POST http://localhost:8000/transform \
  -F "file=@/path/to/your/document.pdf"
```

## License

See LICENSE file for details.
