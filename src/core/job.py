from typing import Optional, TypedDict
import os
from datetime import datetime

from .image_generator import generate_countdown_image
from .ig_publisher import publish_to_instagram
from .discord_publisher import publish_to_discord
from .cloudinary_uploader import upload_image_to_cloudinary, delete_from_cloudinary
from .fb_publisher import publish_to_facebook


class JobConfig(TypedDict):
    exam_date_time: str
    exam_name: str
    instagram_account_id: str | None
    instagram_access_token: str | None
    instagram_enabled: bool
    facebook_access_token: str | None
    facebook_page_id: str | None
    facebook_enabled: bool
    discord_webhook_url: str | None
    discord_enabled: bool



class JobResult(TypedDict):
    success: bool
    days_left: int | None
    image_path: str | None
    ig_status: str
    fb_status: str
    discord_status: str
    error: Optional[str]


def _cleanup_output_dir(output_dir: str, keep:int)->None:
    try:
        files = [
            os.path.join(output_dir, f)
            for f in os.listdir(output_dir)
            if f.startswith("countdown_") and f.endswith(".jpg")
        ]
        files.sort(key=os.path.getmtime,reverse=True)
        for old in files[keep:]:
            try:
                os.remove(old)
            except OSError:
                pass
    except OSError as e:
        print(f"[Warning] Failed to clean up old images in output directory: {e}")



def run_job(
    config: JobConfig, dry_run: bool = False, run_log_id: int | None = None
) -> JobResult:
    exam_name = config["exam_name"]
    ig_account_id = config["instagram_account_id"]
    ig_access_token = config["instagram_access_token"]
    ig_enabled = config["instagram_enabled"]
    facebook_page_id = config["facebook_page_id"]
    facebook_access_token = config["facebook_access_token"]
    facebook_enabled = config["facebook_enabled"]
    discord_webhook_url = config["discord_webhook_url"]
    discord_enabled = config["discord_enabled"]

    # Calculate days
    today = datetime.now()

    exam_datetime_str = config["exam_date_time"]

    try:
        if len(exam_datetime_str.strip()) > 10:
            exam_date = datetime.strptime(exam_datetime_str, "%Y-%m-%d %H:%M:%S")
        else:
            exam_date = datetime.strptime(exam_datetime_str, "%Y-%m-%d")
        days_left = (exam_date.date() - today.date()).days

    except ValueError:
        return JobResult(
            success=False,
            days_left=None,
            image_path=None,
            ig_status="skipped",
            fb_status="skipped",
            discord_status="skipped",
            error=f"Exam date: {exam_datetime_str} is invalid, please use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS",
        )

    # Generate countdown image
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(BASE_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)
    if run_log_id is not None:
        image_filename = f"countdown_{run_log_id}.jpg"
    else:
        image_filename = f"countdown_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    local_image_path = os.path.join(output_dir, image_filename)

    try:
        generate_countdown_image(
            days_left=days_left,
            output_path=local_image_path,
            bg_path=os.path.join(BASE_DIR, "assets", "116.png"),
            font_path=os.path.join(BASE_DIR, "assets", "arialroundedmtbold.ttf"),
        )
    except Exception as e:
        return JobResult(
            success=False,
            days_left=days_left,
            image_path=None,
            ig_status="skipped",
            fb_status="skipped",
            discord_status="skipped",
            error=f"An error occurred while generating countdown image: {e}",
        )

    if dry_run:
        _cleanup_output_dir(output_dir, keep=30)
        return JobResult(
            success=True,
            days_left=days_left,
            image_path=local_image_path,
            ig_status="skipped",
            fb_status="skipped",
            discord_status="skipped",
            error=None,
        )

    # Upload image to Cloudinary to get a public URL for Instagram Graph API
    try:
        public_image_url, public_id = upload_image_to_cloudinary(local_image_path)
    except Exception as e:
        return JobResult(
            success=False,
            days_left=days_left,
            image_path=None,
            ig_status="skipped",
            fb_status="skipped",
            discord_status="skipped",
            error=f"An error occurred while uploading image to Cloudinary: {e}",
        )

    result = JobResult(
        success=True,
        days_left=days_left,
        image_path=local_image_path,
        ig_status="skipped",
        fb_status="skipped",
        discord_status="skipped",
        error=None,
    )
    caption = f"#{exam_name}倒數 {days_left} 天！大家準備好了嗎？ 📚✍️\n\n#倒數計時 #考試倒數 #考試加油 #{exam_name}"
    # Publish to Instagram
    if  ig_enabled and ig_account_id and ig_access_token:
        print("[Info] Posting to Instagram...")
        try:
            publish_to_instagram(
                ig_account_id=ig_account_id,
                access_token=ig_access_token,
                image_url=public_image_url,
                caption=caption,
            )
            result["ig_status"] = "posted"
        except Exception as e:
            result["ig_status"] = f"error: {e}"

    # Publish to Facebook
    if facebook_enabled and facebook_page_id and facebook_access_token:
        print("[Info] Posting to Facebook...")
        try:
            publish_to_facebook(
                page_id=facebook_page_id,
                access_token=facebook_access_token,
                image_url=public_image_url,
                caption=caption,
            )
            result["fb_status"] = "posted"
        except Exception as e:
            result["fb_status"] = f"error: {e}"

    # Publish to Discord
    if discord_enabled and discord_webhook_url:
        try:
            publish_to_discord(discord_webhook_url, local_image_path, caption)
            result["discord_status"] = "posted"
        except Exception as e:
            result["discord_status"] = f"error: {e}"
    _cleanup_output_dir(output_dir, keep=30)
    delete_from_cloudinary(public_id)
    return result
