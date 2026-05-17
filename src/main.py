import os
import argparse
from datetime import datetime
from dotenv import load_dotenv
import schedule
import time

from image_generator import generate_countdown_image
from ig_publisher import upload_image_to_cloudinary, publish_to_instagram
from discord_publisher import publish_to_discord

def job(args):
    # Load environment variables   
    exam_name = os.getenv("EXAM_NAME", "期末考")
    ig_account_id = os.getenv("IG_ACCOUNT_ID")
    ig_access_token = os.getenv("IG_ACCESS_TOKEN")
    discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    print('[Info] Countdown job started.')
    
    if not args.dry_run and (not ig_account_id or not ig_access_token):
        print("[Error] Instagram account ID or access token is not set. Please check your environment variables.")
        return

    # Calculate days
    today = datetime.now()
    
    exam_datetime_str = os.getenv("EXAM_DATETIME") or os.getenv("EXAM_DATE", "2026-07-01")
    
    try:
        if len(exam_datetime_str.strip()) > 10:
            exam_date = datetime.strptime(exam_datetime_str, "%Y-%m-%d %H:%M:%S")
        else:
            exam_date = datetime.strptime(exam_datetime_str, "%Y-%m-%d")
        days_left = (exam_date.date() - today.date()).days
            
    except ValueError:
        print(f"[Error] Exam date: {exam_datetime_str} is invalid, please use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS")
        return

    print(f"[Info] 距離 {exam_name} 還有 {days_left} 天")

    # 3. 產生圖片
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(BASE_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)
    local_image_path = os.path.join(output_dir, f"countdown_{days_left}.jpg")
    
    print("[Info] Generating countdown image...")
    generate_countdown_image(
        days_left=days_left,
        output_path=local_image_path,
        bg_path=os.path.join(BASE_DIR, "assets", "116.png"),
        font_path=os.path.join(BASE_DIR, "assets", "arialroundedmtbold.ttf")
    )
    
    if args.dry_run:
        print("[Info] Dry run mode: Image generated, skipping upload and posting.")
        return

    # Upload image to Cloudinary to get a public URL for Instagram Graph API
    public_image_url = upload_image_to_cloudinary(local_image_path)
    
    # Publish to Instagram
    caption = f"#{exam_name}倒數 {days_left} 天！大家準備好了嗎？ 📚✍️\n\n#倒數計時 #考試倒數 #考試加油 #{exam_name}"
    print("[Info] Posting to Instagram...")
    assert ig_account_id and ig_access_token
    try:
        publish_to_instagram(
            ig_account_id=ig_account_id,
            access_token=ig_access_token,
            image_url=public_image_url,
            caption=caption
        )
    except Exception as e:
        print(f"[Error] An error occurred while posting to Instagram: {e}")

    # Publish to Discord
    if discord_webhook_url:
        publish_to_discord(discord_webhook_url, local_image_path, caption)
        
    if os.path.exists(local_image_path):
        os.remove(local_image_path)
        print(f"[Info] Cleaned local file: {local_image_path}")

def main():
    load_dotenv()
    
    schedule_time = os.getenv("SCHEDULE_TIME", "07:00")
    parser = argparse.ArgumentParser(description="Instagram Countdown Bot")
    parser.add_argument("--dry-run", action="store_true", help="Generate image but skip uploading and posting")
    args = parser.parse_args()
    if args.dry_run:
        print("[Info] Starting Dry run mode: Will only generate image, skipping upload and posting.")
        job(args)
        return
    schedule.every().day.at(schedule_time).do(job, args=args)
    print(f"[Info] Countdown bot has scheduled to run daily at {schedule_time}")
    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    main()
