from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from markitdown import MarkItDown, MarkItDownException, UnsupportedFormatException, FileConversionException
import io

app = FastAPI()

# Initialize MarkItDown converter
md = MarkItDown()

# Maximum file size: 30MB
MAX_FILE_SIZE = 30 * 1024 * 1024

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/transform")
async def transform(file: UploadFile = File(...)):
    """
    Transform uploaded file to markdown format.
    
    Args:
        file: Uploaded file (form data field name: 'file')
    
    Returns:
        JSON with markdown content and optional title
    """
    try:
        # Read file content
        content = await file.read()
        
        # Validate file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE // (1024 * 1024)}MB"
            )
        
        # Create BytesIO stream from content
        file_stream = io.BytesIO(content)
        
        # Get file extension for hint
        file_extension = None
        if file.filename:
            if '.' in file.filename:
                file_extension = '.' + file.filename.rsplit('.', 1)[1].lower()
        
        # Convert to markdown
        result = md.convert_stream(
            file_stream,
            file_extension=file_extension
        )
        
        # Return response
        response_data = {
            "markdown": result.markdown,
            "title": result.title
        }
        
        return JSONResponse(content=response_data)
        
    except UnsupportedFormatException as e:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file format: {str(e)}"
        )
    except FileConversionException as e:
        raise HTTPException(
            status_code=422,
            detail=f"File conversion failed: {str(e)}"
        )
    except MarkItDownException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Conversion error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
