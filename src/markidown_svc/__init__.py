import io
import os

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from markitdown import (
    FileConversionException,
    MarkItDown,
    MarkItDownException,
    UnsupportedFormatException,
)

app = FastAPI()

# Initialize MarkItDown converter
md = MarkItDown()

# Maximum file size: 30MB
MAX_FILE_SIZE = 30 * 1024 * 1024

# Load valid API keys from environment variable
VALID_API_KEYS = set(
    key.strip() for key in os.getenv("APIKEY", "").split(",") if key.strip()
)


def validate_api_key(api_key: str | None) -> bool:
    """
    Validate the API key against the list of valid keys.

    Args:
        api_key: The API key from the X-Apikey header

    Returns:
        True if valid, False otherwise
    """
    if not VALID_API_KEYS:
        # If no API keys are configured, allow all requests
        return True
    if not api_key:
        return False
    return api_key in VALID_API_KEYS


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/transform")
async def transform(
    file: UploadFile = File(...), x_apikey: str | None = Header(None, alias="X-Apikey")
):
    """
    Transform uploaded file to markdown format.

    Args:
        file: Uploaded file (form data field name: 'file')
        x_apikey: API key from X-Apikey header

    Returns:
        JSON with markdown content and optional title
    """
    # Validate API key
    if not validate_api_key(x_apikey):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
        )

    try:
        # Read file content
        content = await file.read()

        # Validate file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE // (1024 * 1024)}MB",
            )

        # Create BytesIO stream from content
        file_stream = io.BytesIO(content)

        # Get file extension for hint
        file_extension = None
        if file.filename:
            if "." in file.filename:
                file_extension = "." + file.filename.rsplit(".", 1)[1].lower()

        # Convert to markdown
        result = md.convert_stream(file_stream, file_extension=file_extension)

        # Return response
        response_data = {"markdown": result.markdown, "title": result.title}

        return JSONResponse(content=response_data)

    except UnsupportedFormatException as e:
        raise HTTPException(
            status_code=415, detail=f"Unsupported file format: {str(e)}"
        )
    except FileConversionException as e:
        raise HTTPException(status_code=422, detail=f"File conversion failed: {str(e)}")
    except MarkItDownException as e:
        raise HTTPException(status_code=500, detail=f"Conversion error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
