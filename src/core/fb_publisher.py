import time
import requests


def publish_to_facebook(page_id: str, access_token: str, image_url: str, caption: str):
    """
    Publish an image to Facebook using the Graph API (POST to /{page_id}/photos)
    """
    api_version = "v25.0"
    base_url = f"https://graph.facebook.com/{api_version}"

    print("[Info] Posting to Facebook...")
    url = f"{base_url}/{page_id}/photos"
    payload = {
        "url": image_url,
        "caption": caption,
        "access_token": access_token,
        "published": True,
    }

    res = requests.post(url, data=payload)
    if res.status_code != 200:
        raise RuntimeError(f"[Error] Failed to create Facebook post: {res.text}")

    post_id = res.json().get("post_id") or res.json().get("id")
    print(f"[Success] Facebook post created successfully, ID: {post_id}")
    return post_id


def test_facebook(page_id: str, access_token: str):
    """
    Test function to verify Facebook credentials by fetching the page's information.
    """
    try:
        api_version = "v25.0"
        base_url = f"https://graph.facebook.com/{api_version}"
        url = f"{base_url}/{page_id}"

        res = requests.get(
            url, params={"fields": "id,name", "access_token": access_token}, timeout=10
        )
        if res.status_code == 200:
            data = res.json()
            return True, f"Facebook credentials are valid. Page ID: {data.get('id')}, Name: {data.get('name')}"
        return False, f"Failed to validate Facebook credentials: {res.text}"
    except Exception as e:
        return False, f"An error occurred while validating Facebook credentials: {e}"