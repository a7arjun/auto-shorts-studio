"""Local transparent chibi assets, loaded once per process."""
from functools import lru_cache
import json
from pathlib import Path
from PIL import Image

ASSET_ROOT=Path(__file__).resolve().parents[1]/'assets/pokemon'


@lru_cache(maxsize=32)
def character_image(species):
    manifest=json.loads((ASSET_ROOT/'manifest.json').read_text())
    entry=manifest['entries'].get(species)
    if not entry:
        return None
    if not entry.get('source_url') or not entry.get('usage_basis'):
        raise ValueError('Character asset needs its source and documented usage basis')
    file=(ASSET_ROOT/entry['file']).resolve()
    if ASSET_ROOT.resolve() not in file.parents or file.suffix.lower() not in ('.png','.webp'):
        raise ValueError('Invalid character image path')
    with Image.open(file) as source:
        image=source.convert('RGBA')
        image.thumbnail((230,230),Image.Resampling.LANCZOS)
        return image.copy()
