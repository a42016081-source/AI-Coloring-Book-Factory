"""Provider-agnostic image generation with retry & fallback."""
import io
import logging
import time
import urllib.parse
from typing import Optional
import requests
from PIL import Image
from config import Config

logger = logging.getLogger(__name__)


class ImageGenerationError(Exception):
    pass


# ---------------- PROVIDER IMPLEMENTATIONS ----------------

def _gen_pollinations(prompt: str, width: int = 1024, height: int = 1024,
                     timeout: int = 60) -> bytes:
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}"
    params = {"width": width, "height": height, "nologo": "true", "model": "flux"}
    r = requests.get(url, params=params, timeout=timeout)
    if r.status_code != 200:
        raise ImageGenerationError(f"Pollinations HTTP {r.status_code}")
    return r.content


def _gen_huggingface(prompt: str, timeout: int = 90) -> bytes:
    if not Config.HF_TOKEN:
        raise ImageGenerationError("HF_TOKEN not configured")
    from huggingface_hub import InferenceClient
    client = InferenceClient(token=Config.HF_TOKEN)
    img = client.text_to_image(prompt, model="black-forest-labs/FLUX.1-schnell")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _gen_gemini(prompt: str, timeout: int = 60) -> bytes:
    if not Config.GEMINI_API_KEY:
        raise ImageGenerationError("GEMINI_API_KEY not configured")
    # Note: Gemini's public image generation is limited; using text-to-image
    # via the Gemini generative API when available. Falls back gracefully.
    try:
        import google.generativeai as genai
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash-exp-image-generation")
        resp = model.generate_content(prompt)
        for part in resp.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                return part.inline_data.data
        raise ImageGenerationError("No image in Gemini response")
    except Exception as e:
        raise ImageGenerationError(f"Gemini failed: {e}")


def _gen_custom(prompt: str, timeout: int = 60) -> bytes:
    if not Config.CUSTOM_IMAGE_API_URL:
        raise ImageGenerationError("CUSTOM_IMAGE_API_URL not set")
    headers = {"Content-Type": "application/json"}
    if Config.CUSTOM_IMAGE_API_KEY:
        headers["Authorization"] = f"Bearer {Config.CUSTOM_IMAGE_API_KEY}"
    payload = {"prompt": prompt, "n": 1, "size": "1024x1024"}
    r = requests.post(Config.CUSTOM_IMAGE_API_URL, json=payload,
                      headers=headers, timeout=timeout)
    if r.status_code != 200:
        raise ImageGenerationError(f"Custom API HTTP {r.status_code}")
    ct = r.headers.get("content-type", "")
    if "image" in ct:
        return r.content
    data = r.json()
    if "data" in data and data["data"]:
        url = data["data"][0].get("url") or data["data"][0].get("b64_json")
        if url and url.startswith("http"):
            return requests.get(url, timeout=timeout).content
    raise ImageGenerationError("Unexpected custom API response")


_PROVIDER_MAP = {
    "pollinations": _gen_pollinations,
    "huggingface": _gen_huggingface,
    "gemini": _gen_gemini,
    "custom": _gen_custom,
}


# ---------------- PUBLIC API ----------------

def generate_image(prompt: str, provider: str = "pollinations",
                   retries: int = 3, fallback: bool = True) -> bytes:
    """Returns PNG bytes. Tries provider, then retries, then fallback."""
    order = [provider] if not fallback else [provider, "pollinations", "huggingface"]
    last_err = None
    for prov in order:
        if prov not in _PROVIDER_MAP:
            continue
        for attempt in range(1, retries + 1):
            try:
                logger.info("Generating with %s (attempt %d)", prov, attempt)
                data = _PROVIDER_MAP[prov](prompt)
                # Validate it's a real image
                img = Image.open(io.BytesIO(data))
                img.verify()
                return data
            except Exception as e:
                last_err = e
                logger.warning("%s attempt %d failed: %s", prov, attempt, e)
                time.sleep(1.5 * attempt)
    raise ImageGenerationError(f"All providers failed. Last error: {last_err}")


def to_coloring_page(png_bytes: bytes, black_white: bool = True,
                     border: bool = True) -> Image.Image:
    """Convert generated image to a clean coloring-page style."""
    img = Image.open(io.BytesIO(png_bytes)).convert("L")
    if black_white:
        # Threshold to pure black/white
        img = img.point(lambda x: 0 if x < 200 else 255, "1").convert("L")
    if border:
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        w, h = img.size
        margin = int(min(w, h) * 0.03)
        draw.rectangle([margin, margin, w - margin, h - margin], outline=0, width=3)
    return img