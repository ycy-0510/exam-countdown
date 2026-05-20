from pathlib import Path
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import Response, FileResponse
from core.image_generator import generate_countdown_image
from PIL import Image

router = APIRouter(prefix="/config/template", tags=["config", "template"])

ASSETS_DIR = (Path(__file__).resolve().parent.parent.parent / "assets").resolve()


@router.get("/preview", response_class=Response)
def get_template_preview():
    font_path = ASSETS_DIR / "arialroundedmtbold.ttf"
    # Get jpeg or png (etx: jpeg, jpg, png)
    current_bg: str | None = None
    for ext in ["jpeg", "jpg", "png"]:
        current_path = ASSETS_DIR / f"current.{ext}"
        if current_path.exists():
            current_bg = str(current_path)
            break
    templateByte = generate_countdown_image(
        days_left=987, bg_path=current_bg, font_path=str(font_path)
    )
    return Response(content=templateByte.getvalue(), media_type="image/jpeg")


@router.get("/current", response_class=FileResponse)
def get_current_template():
    # Get jpeg or png (etx: jpeg, jpg, png)
    for ext in ["jpeg", "jpg", "png"]:
        current_path = ASSETS_DIR / f"current.{ext}"
        if current_path.exists():
            return FileResponse(path=current_path, media_type=f"image/{ext}")

    return Response(content="No template image found", status_code=404)


@router.post("")
def upload_current(uploaded_file: UploadFile = File(...)):
    if uploaded_file.filename is None:
        return Response(content="No file uploaded", status_code=400)
    if uploaded_file.size is None or uploaded_file.size == 0:
        return Response(content="Uploaded file is empty", status_code=400)
    if uploaded_file.size > 5 * 1024 * 1024:  # Limit file size to 5MB
        return Response(content="Uploaded file is too large (max 5MB)", status_code=400)
    
    ext = uploaded_file.filename.split(".")[-1].lower()

    if ext not in ["jpeg", "jpg", "png"]:
        return Response(
            content="Invalid file type. Only jpeg, jpg, png allowed.", status_code=400
        )

    # Verify with PIL (verify() invalidates the image, so reopen for saving)
    try:
        Image.open(uploaded_file.file).verify()
        uploaded_file.file.seek(0)
        image = Image.open(uploaded_file.file)
        if image.mode != "RGB":
            image = image.convert("RGB")
    except Exception:
        return Response(content="Uploaded file is not a valid image.", status_code=400)

    # Remove existing current.* files
    for existing_ext in ["jpeg", "jpg", "png"]:
        existing_path = ASSETS_DIR / f"current.{existing_ext}"
        if existing_path.exists():
            existing_path.unlink()

    save_ext = "jpg" if ext in ("jpg", "jpeg") else "png"
    save_format = "JPEG" if save_ext == "jpg" else "PNG"
    save_path = ASSETS_DIR / f"current.{save_ext}"
    image.save(save_path, save_format)
    return Response(content="Template image uploaded successfully", status_code=200)
