from dataclasses import dataclass
from typing import Dict, Tuple

from PIL import Image, ImageDraw, ImageFont

CANVAS_SIZE: Tuple[int, int] = (960, 540)
FEATURE_CHOICES: Tuple[str, ...] = (
    "email_manual",
    "email_automatic",
    "drive_share",
    "multi_mode",
    "deliverability",
    "attachments",
    "compliance",
    "tracking",
)


@dataclass(frozen=True)
class LayoutSpec:
    guard_focus: Tuple[str, ...]
    accent_color: Tuple[int, int, int] = (56, 189, 248)


LAYOUT_SPECS: Dict[str, LayoutSpec] = {
    "email_manual": LayoutSpec(
        guard_focus=("email_manual", "deliverability", "tracking"),
    ),
    "email_automatic": LayoutSpec(
        guard_focus=("email_automatic", "deliverability", "attachments", "tracking"),
        accent_color=(74, 222, 128),
    ),
    "drive_share": LayoutSpec(
        guard_focus=("drive_share", "deliverability", "compliance"),
        accent_color=(129, 140, 248),
    ),
    "multi_mode": LayoutSpec(
        guard_focus=("multi_mode", "email_manual", "drive_share"),
        accent_color=(251, 191, 36),
    ),
}



def _load_font() -> ImageFont.ImageFont:
    try:
        return ImageFont.load_default()
    except Exception:  # pragma: no cover - fallback for rare PIL issues
        return ImageFont.load_default()


def create_blueprint(layout_name: str) -> Image.Image:
    if layout_name not in LAYOUT_SPECS:
        raise ValueError(f"Unknown layout requested: {layout_name}")

    spec = LAYOUT_SPECS[layout_name]
    image = Image.new("RGB", CANVAS_SIZE, "white")
    draw = ImageDraw.Draw(image)
    width, height = CANVAS_SIZE

    border_color = (15, 23, 42)
    draw.rectangle((0, 0, width - 1, height - 1), outline=border_color, width=4)

    font = _load_font()
    header = layout_name.replace("_", " ").title()
    draw.text((32, 32), header, fill=border_color, font=font)

    y = 120
    for item in spec.guard_focus:
        bullet = f"- {item.replace('_', ' ').title()}"
        draw.text((48, y), bullet, fill=(30, 41, 59), font=font)
        y += 36

    badge_text = "Guard Focus"
    badge_width = 200
    badge_height = 48
    badge_x = width - badge_width - 48
    badge_y = 32
    badge_color = spec.accent_color
    draw.rounded_rectangle(
        (badge_x, badge_y, badge_x + badge_width, badge_y + badge_height),
        radius=16,
        fill=badge_color,
    )
    draw.text((badge_x + 24, badge_y + 12), badge_text, fill="black", font=font)

    return image
