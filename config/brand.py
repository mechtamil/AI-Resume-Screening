"""ALTEN-aligned visual design tokens used by RecruitOS.

The verified color values originate from ALTEN's public Logo & Colors
Guidelines.  Keeping the values in one module allows a future 2025 brandbook
revision to be applied without rewriting page code.
"""
from __future__ import annotations

from pathlib import Path

from config.paths import PROJECT_ROOT

BRAND_NAME = "ALTEN"
PRODUCT_NAME = "RecruitOS"
PRODUCT_TAGLINE = "Intelligent recruitment. Precisely ranked."

# Verified ALTEN corporate colors.
ALTEN_NAVY = "#043962"
ALTEN_BLUE = "#008BD2"
ALTEN_LIGHT_BLUE = "#7ECBEE"
ALTEN_RED = "#E30513"
ALTEN_YELLOW = "#FFED00"
ALTEN_AMBER = "#FFBA00"
ALTEN_BLACK = "#000000"
ALTEN_DARK_GREY = "#484848"
ALTEN_GREY = "#8C8C9A"
ALTEN_SILVER = "#C0C0C8"
ALTEN_PALE_GREY = "#E6E6E9"
ALTEN_WHITE = "#FFFFFF"

# Supporting blue shades from the published palette.
ALTEN_BLUE_DEEP = "#0C5CCE"
ALTEN_BLUE_MID = "#0070C0"
ALTEN_BLUE_SKY = "#67B7F6"
ALTEN_BLUE_SOFT = "#B3DBFB"
ALTEN_BLUE_ICE = "#D5E6FD"

# Approved public assets. Deployments can replace these URLs with approved
# local files in assets/brand without changing UI code.
ALTEN_LOGO_BLACK_URL = (
    "https://www.alten.com/wp-content/uploads/2019/03/"
    "LOGO_Alten_Couleurs_Black.png"
)
ALTEN_LOGO_WHITE_URL = (
    "https://www.alten.com/wp-content/uploads/2019/03/"
    "LOGO_Alten_Couleurs_White.png"
)

BRAND_ASSET_DIR = PROJECT_ROOT / "assets" / "brand"
ALTEN_LOGO_BLACK_LOCAL = BRAND_ASSET_DIR / "alten_logo_black.png"
ALTEN_LOGO_WHITE_LOCAL = BRAND_ASSET_DIR / "alten_logo_white.png"


def preferred_logo_path(*, dark_background: bool) -> Path | None:
    """Return an approved local ALTEN logo when one has been supplied."""
    candidate = ALTEN_LOGO_WHITE_LOCAL if dark_background else ALTEN_LOGO_BLACK_LOCAL
    return candidate if candidate.is_file() else None


def preferred_logo_url(*, dark_background: bool) -> str:
    """Return the official public fallback logo URL."""
    return ALTEN_LOGO_WHITE_URL if dark_background else ALTEN_LOGO_BLACK_URL
