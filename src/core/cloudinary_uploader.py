import os
import cloudinary
import cloudinary.uploader

def upload_image_to_cloudinary(image_path: str) -> tuple[str, str]:
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
        public_id = response.get('public_id')   
        if not secure_url or not public_id:
            raise ValueError("[Error] Upload successful but no secure_url or public_id")
        print(f"[Success] Image uploaded successfully: {secure_url}")
        return secure_url, public_id
    except Exception as e:
        raise RuntimeError(f"[Error] Cloudinary upload failed: {e}")
    
def delete_from_cloudinary(public_id: str)->bool:
    """
    Delete an image from Cloudinary using its public ID.
    """
    try:
        response = cloudinary.uploader.destroy(public_id)
        result = response.get('result')
        if result == 'ok':
            print(f"[Info] Deleted image from Cloudinary: {public_id}")
            return True
        print(f"[Warning] Failed to delete image from Cloudinary: {public_id}, response: {response}")
        return False
    except Exception as e:
        print(f"[Error] Cloudinary deletion failed for {public_id}: {e}")
        return False