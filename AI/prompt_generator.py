"""Generates unique prompts per page and per book."""
import json
import random
import logging
import requests
from config import Config
from pathlib import Path
from typing import List

PROMPTS_FILE = Path(__file__).resolve().parent.parent / "Settings" / "prompts.json"
logger = logging.getLogger(__name__)


def _load_prompts() -> dict:
    with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_page_prompts(topic: str, count: int, style: str, age: str,
                          difficulty: str, language: str = "English") -> List[str]:
    data = _load_prompts()
    templates = data["topic_templates"].get(topic, [topic])
    base = data["base_prompt"]
    seen = set()
    prompts = []
    attempts = 0
    while len(prompts) < count and attempts < count * 10:
        attempts += 1
        subject = random.choice(templates)
        variant = random.choice([
            "sitting", "playing", "in a garden", "with a friend",
            "smiling", "simple pose", "close-up", "full body",
        ])
        p = base.format(
            topic=f"{subject} {variant}",
            style=style,
            age=age,
            difficulty=difficulty,
        )
        if language == "Hindi":
            p += ", Indian style motifs"
        if p not in seen:
            seen.add(p)
            prompts.append(p)
    while len(prompts) < count:
        prompts.append(f"{base.format(topic=topic, style=style, age=age, difficulty=difficulty)} variation {len(prompts)+1}")
    return prompts



def _enhance_prompts_with_nvidia(prompts: List[str], topic: str, style: str,
                                age: str, timeout: int = 90) -> List[str]:
    """Optionally refine the page prompts with NVIDIA Llama; fail open."""
    if not (Config.NVIDIA_API_KEY and Config.NVIDIA_PROMPT_ENHANCEMENT):
        return prompts
    if not prompts:
        return prompts

    headers = {
        "Authorization": f"Bearer {Config.NVIDIA_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    system = (
        "You write safe, detailed image-generation prompts for children's coloring-book pages. "
        "Return ONLY a valid JSON object with a 'prompts' array containing exactly the same "
        "number of entries as the input. Keep every prompt as a single string. "
        "Specify clean black line art, white background, bold smooth outlines, no color, "
        "no shading, no text, no watermark, one clear main subject, age-appropriate content."
    )
    user = {
        "topic": topic,
        "art_style": style,
        "target_age": age,
        "prompts_to_improve": prompts,
    }
    payload = {
        "model": Config.NVIDIA_CHAT_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": str(user)},
        ],
        "temperature": 0.35,
        "top_p": 0.7,
        "max_tokens": min(4096, max(800, len(prompts) * 180)),
    }
    try:
        response = requests.post(
            Config.NVIDIA_CHAT_URL, headers=headers, json=payload, timeout=timeout
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        # Be tolerant if the model wraps JSON in a markdown code fence.
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1]
            if content.endswith("```"):
                content = content[:-3].strip()
        import json
        parsed = json.loads(content)
        improved = parsed.get("prompts") if isinstance(parsed, dict) else None
        if (isinstance(improved, list) and len(improved) == len(prompts)
                and all(isinstance(item, str) and item.strip() for item in improved)):
            logger.info("Enhanced %d coloring prompts with NVIDIA Llama", len(improved))
            return [item.strip() for item in improved]
        logger.warning("NVIDIA Llama returned an unexpected prompt list; using local prompts")
    except Exception as exc:
        logger.warning("NVIDIA Llama prompt enhancement skipped: %s", exc)
    return prompts


def generate_cover_prompt(topic: str, style: str, title: str = "") -> str:
    data = _load_prompts()
    return data["cover_prompt"].format(topic=topic, style=style)


def generate_back_prompt(topic: str) -> str:
    data = _load_prompts()
    return data["back_prompt"].format(topic=topic)
