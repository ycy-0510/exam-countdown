import os
import time
import requests
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

def publish_to_instagram(ig_account_id: str, access_token: str, image_url: str, caption: str):
    """
    使用 Facebook Graph API 發佈圖片到 Instagram (兩步驟: 建立 Container -> Publish)
    """
    api_version = "v25.0"
    base_url = f"https://graph.instagram.com/{api_version}"
    
    # 1. Create Media Container
    print("[Info] Creating Media Container...")
    container_url = f"{base_url}/{ig_account_id}/media"
    container_payload = {
        'image_url': image_url,
        'caption': caption,
        'access_token': access_token
    }
    
    container_res = requests.post(container_url, data=container_payload)
    if container_res.status_code != 200:
        raise RuntimeError(f"[Error] Failed to create Media Container: {container_res.text}")
        
    container_id = container_res.json().get('id')
    print(f"[Success] Media Container created successfully, ID: {container_id}")
    
    # Instagram 建議稍等一下讓系統處理圖片
    time.sleep(3)
    
    # 2. Publish the Container
    print("[Info] Publishing Container to Instagram...")
    publish_url = f"{base_url}/{ig_account_id}/media_publish"
    publish_payload = {
        'creation_id': container_id,
        'access_token': access_token
    }
    
    publish_res = requests.post(publish_url, data=publish_payload)
    if publish_res.status_code != 200:
        raise RuntimeError(f"[Error] Failed to publish to Instagram: {publish_res.text}")
        
    post_id = publish_res.json().get('id')
    print(f"[Success] Post published successfully! Post ID: {post_id}")
    return post_id
