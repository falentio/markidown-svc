import asyncio
import io
import json
import os
from typing import AsyncGenerator

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
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


@app.post("/transform-stream")
async def transform_stream(
    file: UploadFile = File(...), x_apikey: str | None = Header(None, alias="X-Apikey")
):
    """
    Transform uploaded file to markdown format with streaming status updates.

    Args:
        file: Uploaded file (form data field name: 'file')
        x_apikey: API key from X-Apikey header

    Returns:
        Server-Sent Events stream with status updates every 5 seconds until conversion completes
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

        async def event_generator() -> AsyncGenerator[str, None]:
            """Generate server-sent events for streaming response."""
            conversion_done = False
            result_data = None
            error_data = None

            # Start conversion in background
            async def convert():
                nonlocal conversion_done, result_data, error_data
                try:
                    # Convert to markdown (blocking operation)
                    result = await asyncio.to_thread(
                        md.convert_stream, file_stream, file_extension=file_extension
                    )
                    result_data = {"markdown": result.markdown, "title": result.title}
                except UnsupportedFormatException as e:
                    error_data = {
                        "error": "Unsupported file format",
                        "detail": str(e),
                        "status_code": 415,
                    }
                except FileConversionException as e:
                    error_data = {
                        "error": "File conversion failed",
                        "detail": str(e),
                        "status_code": 422,
                    }
                except MarkItDownException as e:
                    error_data = {
                        "error": "Conversion error",
                        "detail": str(e),
                        "status_code": 500,
                    }
                except Exception as e:
                    error_data = {
                        "error": "Internal server error",
                        "detail": str(e),
                        "status_code": 500,
                    }
                finally:
                    conversion_done = True

            # Start conversion task
            conversion_task = asyncio.create_task(convert())

            # Send status updates every 5 seconds until done
            while not conversion_done:
                yield f"data: {json.dumps({'status': 'pending'})}\n\n"
                await asyncio.sleep(5)

            # Wait for conversion to complete
            await conversion_task

            # Send final result or error
            if error_data:
                yield f"data: {json.dumps(error_data)}\n\n"
            elif result_data:
                yield f"data: {json.dumps(result_data)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
