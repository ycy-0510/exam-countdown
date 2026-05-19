import os
import requests


def publish_to_discord(webhook_url: str, image_path: str, caption: str):
    """
    Post an image with a caption to a Discord channel using a webhook URL.
    """
    if not webhook_url:
        print("[Warning] Discord Webhook URL is not set, skipping Discord posting.")
        return

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"[Error] Image file not found: {image_path}")

    print("[Info] Posting to Discord...")
    try:
        with open(image_path, "rb") as f:
            files = {"file": (os.path.basename(image_path), f, "image/jpeg")}
            payload = {"content": caption}
            response = requests.post(webhook_url, data=payload, files=files)

        if response.status_code in [200, 204]: # Success
            print("[Success] Image posted to Discord successfully.")
        else:
            raise RuntimeError(
                f"[Error] Discord API returned error code {response.status_code}: {response.text}"
            )
    except Exception as e:
        print(f"[Error] An error occurred while posting to Discord: {e}")

def test_discord(webhook_url: str):
    """
    Test function to verify Discord webhook URL.
    """
    try:
        response = requests.post(webhook_url, data={"content": "Test message from Exam Countdown app."})
        if response.status_code in [200, 204]:
            return True, "Discord webhook URL is valid."
        else:
            return False, f"Failed to validate Discord webhook URL: {response.text}"
    except Exception as e:
        return False, f"An error occurred while validating Discord webhook URL: {e}"