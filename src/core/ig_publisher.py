import time
import requests


def publish_to_instagram(
    ig_account_id: str, access_token: str, image_url: str, caption: str
):
    """
    Publish an image to Instagram using the Facebook Graph API (two steps: Create Container -> Publish)
    """
    api_version = "v25.0"
    base_url = f"https://graph.instagram.com/{api_version}"

    # 1. Create Media Container
    print("[Info] Creating Media Container...")
    container_url = f"{base_url}/{ig_account_id}/media"
    container_payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": access_token,
    }

    container_res = requests.post(container_url, data=container_payload)
    if container_res.status_code != 200:
        raise RuntimeError(
            f"[Error] Failed to create Media Container: {container_res.text}"
        )

    container_id = container_res.json().get("id")
    print(f"[Success] Media Container created successfully, ID: {container_id}")

    # Instagram 建議稍等一下讓系統處理圖片
    time.sleep(3)

    # 2. Publish the Container
    print("[Info] Publishing Container to Instagram...")
    publish_url = f"{base_url}/{ig_account_id}/media_publish"
    publish_payload = {"creation_id": container_id, "access_token": access_token}

    publish_res = requests.post(publish_url, data=publish_payload)
    if publish_res.status_code != 200:
        raise RuntimeError(
            f"[Error] Failed to publish to Instagram: {publish_res.text}"
        )

    post_id = publish_res.json().get("id")
    print(f"[Success] Post published successfully! Post ID: {post_id}")
    return post_id


def test_instagram(
    ig_account_id: str, access_token: str
) -> tuple[bool, str, str | None]:
    """
    Test function to verify Instagram credentials by fetching the account's media.
    """
    try:
        api_version = "v25.0"
        base_url = f"https://graph.instagram.com/{api_version}"
        url = f"{base_url}/{ig_account_id}"

        res = requests.get(
            url,
            params={"fields": "id,username", "access_token": access_token},
            timeout=10,
        )
        if res.status_code == 200:
            data = res.json()
            return (
                True,
                f"Connected as @{data.get('username')} (ID: {data.get('id')})",
                None,
            )
        return False, "Failed to validate Instagram credentials", res.text
    except Exception as e:
        return False, "An error occurred while validating Instagram credentials", str(e)
