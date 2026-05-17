import time
import requests

def publish_to_facebook(page_id: str, access_token: str, image_url: str, caption: str):
    """
    Publish an image to Facebook using the Graph API (POST to /{page_id}/photos)
    """
    api_version = "v25.0"
    base_url = f"https://graph.facebook.com/{api_version}"
    
    # 1. Create Media Container
    print("[Info] Creating Media Container...")
    url = f"{base_url}/{page_id}/photos"
    payload = {
        'url': image_url,
        'message': caption,
        'access_token': access_token
    }
    
    res = requests.post(url, data=payload)
    if res.status_code != 200:
        raise RuntimeError(f"[Error] Failed to create Facebook post: {res.text}")
    
    post_id = res.json().get('post_id') or res.json().get('id')
    print(f"[Success] Facebook post created successfully, ID: {post_id}")
    return post_id
