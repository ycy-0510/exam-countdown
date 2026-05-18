import os
import cloudinary
import cloudinary.uploader

def upload_image_to_cloudinary(image_path: str) -> str:
    """
    Upload an image to Cloudinary and return the secure URL.
    This is used as an intermediary step to get a public URL for the Instagram Graph API.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"[Error] Image file not found: {image_path}")

    print("[Info] Uploading image to Cloudinary (as intermediary for Graph API)...")
    try:
        response = cloudinary.uploader.upload(image_path)
        secure_url = response.get('secure_url')
        if not secure_url:
            raise ValueError("[Error] Upload successful but no secure_url obtained")
        print(f"[Success] Image uploaded successfully: {secure_url}")
        return secure_url
    except Exception as e:
        raise RuntimeError(f"[Error] Cloudinary upload failed: {e}")