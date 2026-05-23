from io import BytesIO
import datetime
import os
from PIL import Image, ImageCms, ImageDraw, ImageFont
import tempfile

WIDTH, HEIGHT = 1080, 1350
DAY_LEFT_TEXT_POS = (WIDTH / 2, HEIGHT / 2 - 50)
DATE_TEXT_POS = (WIDTH - 200, HEIGHT - 50)
DAYS_LEFT_FONT_SIZE = 250
DATE_FONT_SIZE = 50
PRIMARY_COLOR = (255, 255, 255)
WHITE = (99, 201, 206)
DARK1 = (55, 56, 59)
DARK2 = (34, 36, 39)


def _to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


PALETTE = [
    {"name": "Highlight", "hex": _to_hex(WHITE)},
    {"name": "Primary", "hex": _to_hex(PRIMARY_COLOR)},
    {"name": "Card Background", "hex": _to_hex(DARK2)},
    {"name": "Background", "hex": _to_hex(DARK1)},
]


def generate_countdown_image(
    days_left: int,
    output_path: str | None = None,
    bg_path: str | None = None,
    font_path: str | None = None,
) -> BytesIO:
    """
    Generate a countdown image with the specified number of days left, and save it to the given output path.

    Args:
        days_left (int): Remaining days until the event (e.g., exam). If 0 or negative, it will display "D-Day".
        output_path (str): Output file path
        bg_path (str, optional): Background image path
        font_path (str, optional): Font file path (e.g., .ttf)
    """

    src_icc: bytes | None = None
    if bg_path and os.path.exists(bg_path):
        try:
            image = Image.open(bg_path)
            # Get ICC profile if exists for later color management
            src_icc = image.info.get("icc_profile")
            if image.mode != "RGB":
                image = image.convert("RGB")
            image = image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        except Exception as e:
            print(
                f"[Warning] Can't load background image: {e}, using solid color background instead."
            )
            image = _generate_blank_background()
    else:
        image = _generate_blank_background()

    draw = ImageDraw.Draw(image)

    # Set up fonts
    try:
        if font_path and os.path.exists(font_path):
            days_font = ImageFont.truetype(font_path, DAYS_LEFT_FONT_SIZE)
            date_font = ImageFont.truetype(font_path, DATE_FONT_SIZE)
        else:
            raise IOError("Font file not found, using default font.")
    except IOError:
        print(
            "[Warning] Can't load custom font, using default font instead. For better appearance, please provide a valid .ttf font file."
        )
        days_font = ImageFont.load_default(size=DAYS_LEFT_FONT_SIZE)
        date_font = ImageFont.load_default(size=DATE_FONT_SIZE)

    days_text = f'D-{days_left if days_left>0 else "Day"}'

    draw.text(
        DAY_LEFT_TEXT_POS,
        days_text,
        font=days_font,
        fill=WHITE,
        anchor="mm",
    )

    date_text = datetime.date.today().strftime("%Y-%m-%d")
    draw.text(
        DATE_TEXT_POS,
        date_text,
        font=date_font,
        fill=DARK2,
        anchor="mm",
    )

    # Conver color profile if source ICC profile exists
    if src_icc:
        src_profile = ImageCms.ImageCmsProfile(BytesIO(src_icc))
        dst_profile = ImageCms.createProfile("sRGB")
        converted = ImageCms.profileToProfile(
            image, src_profile, dst_profile, outputMode="RGB"
        )
        if converted is not None:
            image = converted
    if output_path is not None:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        image.save(output_path, "JPEG", quality=95, subsampling=0)
        print(f"[Success] Image saved successfully to: {output_path}")

    bytes_io = BytesIO()
    image.save(bytes_io, format="JPEG", quality=95, subsampling=0)
    bytes_io.seek(0)
    return bytes_io


def _generate_blank_background() -> Image.Image:
    """
    Generate a countdown image template with placeholder text, and return the BytesIO object.
    This can be used for testing or as a template for dynamic image generation.
    """
    image = Image.new("RGB", (WIDTH, HEIGHT), DARK1)
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, HEIGHT - 104, WIDTH, HEIGHT], fill=PRIMARY_COLOR)
    return image


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    generate_countdown_image(
        0,
        os.path.join(BASE_DIR, "output", "test.jpg"),
        os.path.join(BASE_DIR, "assets", "useruploads", "current.png"),
        os.path.join(BASE_DIR, "assets", "arialroundedmtbold.ttf"),
    )

    generate_countdown_image(
        days_left=987,
        output_path=os.path.join(BASE_DIR, "output", "test2.jpg"),
        font_path=os.path.join(BASE_DIR, "assets", "arialroundedmtbold.ttf"),
    )
