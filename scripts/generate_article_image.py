#!/usr/bin/env python3
"""
Generate one newsletter article image via xAI Grok Imagine and save it locally.

Usage:
    python scripts/generate_article_image.py --prompt "..." --out assets/article-images/YYYY-MM-DD/slug.png

Requires:
    XAI_API_KEY in the environment, or in a repo-root .env file
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://api.x.ai/v1/images/generations"
DEFAULT_MODEL = "grok-imagine-image"
DEFAULT_ASPECT = "1:1"
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_dotenv(path: Path) -> None:
    """Load KEY=VALUE pairs from a .env file into os.environ (does not override existing)."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def generate_image(prompt: str, model: str, aspect_ratio: str) -> bytes:
    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.environ.get("XAI_API_KEY", "").strip()
    if not api_key:
        raise SystemExit(
            "Error: XAI_API_KEY is not set. Put it in a repo-root .env file "
            "(see .env.example) or set it in the environment, then retry."
        )

    payload = {
        "model": model,
        "prompt": prompt,
        "n": 1,
        "response_format": "b64_json",
        "aspect_ratio": aspect_ratio,
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Error: xAI API HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Error: could not reach xAI API: {exc}") from exc

    data = body.get("data") or []
    if not data:
        raise SystemExit(f"Error: unexpected API response (no data): {body}")

    item = data[0]
    b64 = item.get("b64_json")
    if b64:
        return base64.b64decode(b64)

    url = item.get("url")
    if not url:
        raise SystemExit(f"Error: response missing b64_json and url: {item}")

    try:
        with urllib.request.urlopen(url, timeout=180) as image_response:
            return image_response.read()
    except urllib.error.URLError as exc:
        raise SystemExit(f"Error: could not download image URL: {exc}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a Grok article image for the newsletter.")
    parser.add_argument("--prompt", required=True, help="Image generation prompt")
    parser.add_argument("--out", required=True, help="Output image path (e.g. assets/article-images/2026-07-16/slug.png)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model id (default: {DEFAULT_MODEL})")
    parser.add_argument(
        "--aspect-ratio",
        default=DEFAULT_ASPECT,
        help=f"Aspect ratio (default: {DEFAULT_ASPECT})",
    )
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    image_bytes = generate_image(args.prompt, args.model, args.aspect_ratio)
    out_path.write_bytes(image_bytes)
    print(f"Saved: {out_path} ({len(image_bytes)} bytes)")


if __name__ == "__main__":
    main()
    sys.exit(0)
