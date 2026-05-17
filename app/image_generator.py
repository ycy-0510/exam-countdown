import io
import datetime
import os
from PIL import Image, ImageCms, ImageDraw, ImageFont


def generate_countdown_image(
    days_left: int,
    output_path: str,
    bg_path: str | None = None,
    font_path: str | None = None,
):
    """
    Generate a countdown image with the specified number of days left, and save it to the given output path.

    Args:
        days_left (int): Remaining days until the event (e.g., exam). If 0 or negative, it will display "D-Day".
        output_path (str): Output file path
        bg_path (str, optional): Background image path
        font_path (str, optional): Font file path (e.g., .ttf)
    """
    width, height = 1080, 1350

    src_icc: bytes | None = None
    if bg_path and os.path.exists(bg_path):
        try:
            image = Image.open(bg_path)
            # Get ICC profile if exists for later color management
            src_icc = image.info.get("icc_profile")
            if image.mode != "RGB":
                image = image.convert("RGB")
            image = image.resize((width, height), Image.Resampling.LANCZOS)
        except Exception as e:
            print(f"[Warning] Can't load background image: {e}, using solid color background instead.")
            image = Image.new("RGB", (width, height), (40, 44, 52))
    else:
        image = Image.new("RGB", (width, height), (40, 44, 52))

    draw = ImageDraw.Draw(image)

    # Set up fonts
    try:
        if font_path and os.path.exists(font_path):
            days_font = ImageFont.truetype(font_path, 250)
            date_font = ImageFont.truetype(font_path, 50)
        else:
            raise IOError("Font file not found, using default font.")
    except IOError:
        print(
            "[Warning] Can't load custom font, using default font instead. For better appearance, please provide a valid .ttf font file."
        )
        days_font = ImageFont.load_default(size=250)
        date_font = ImageFont.load_default(size=50)


    days_text = f'D-{days_left if days_left>0 else "Day"}'

    day_text_x = width / 2
    day_text_y = height / 2 - 50
    draw.text(
        (day_text_x, day_text_y), days_text, font=days_font, fill=(99, 201, 206), anchor="mm"
    )

    date_text = datetime.date.today().strftime("%Y-%m-%d")
    day_text_x=width-200
    day_text_y=height-50
    draw.text(
        (day_text_x, day_text_y), date_text, font=date_font, fill=(55, 56, 59), anchor="mm"
    )

    # Conver color profile if source ICC profile exists
    if src_icc:
        src_profile = ImageCms.ImageCmsProfile(io.BytesIO(src_icc))
        dst_profile = ImageCms.createProfile("sRGB")
        converted = ImageCms.profileToProfile(
            image, src_profile, dst_profile, outputMode="RGB"
        )
        if converted is not None:
            image = converted
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    image.save(output_path, "JPEG", quality=95, subsampling=0)
    print(f"[Success] Image saved successfully to: {output_path}")
    return output_path


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    generate_countdown_image(
        0,
        os.path.join(BASE_DIR, "output", "test.jpg"),
        os.path.join(BASE_DIR, "assets", "116.png"),
        os.path.join(BASE_DIR, "assets", "arialroundedmtbold.ttf"),
    )
