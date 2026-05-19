from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/content", tags=["content"])

OUTPUT_DIR = (Path(__file__).resolve().parent.parent.parent / "output").resolve()

@router.get("/{filename}")
async def get_content(filename: str):
    """Serve generated content files (e.g., images) from the output directory and avoid path traversal."""
    if "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not filename.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Only .jpg files are allowed")
    
    target = (OUTPUT_DIR / filename).resolve()

    try:
        target.relative_to(OUTPUT_DIR)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(path=target, media_type="image/jpeg")