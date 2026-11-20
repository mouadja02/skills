"""Azure service icons stored as readable SVG markup. Total icons: 636."""

from base64 import b64encode
import json
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets" / "service-icons"

AZURE_ICONS = {}
for icon_file in sorted(ASSETS.glob("icons-*.json")):
    with icon_file.open(encoding="utf-8") as stream:
        AZURE_ICONS.update(json.load(stream))


def get_icon_data_uri(key: str) -> str:
    """Get data URI for an Azure icon."""
    icon = AZURE_ICONS.get(key.lower().replace("-", "_").replace(" ", "_"))
    if icon:
        payload = b64encode(icon["svg"].encode("utf-8")).decode("ascii")
        return f"data:image/svg+xml;base64,{payload}"
    return ""


def search_icons(query: str) -> list:
    """Search icons by partial name match."""
    q = query.lower().replace("-", "_").replace(" ", "_")
    return [(k, v["name"], v["category"]) for k, v in AZURE_ICONS.items() if q in k]
