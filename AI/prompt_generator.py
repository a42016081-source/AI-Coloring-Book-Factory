"""Generates unique prompts per page and per book."""
import json
import random
from pathlib import Path
from typing import List

PROMPTS_FILE = Path(__file__).resolve().parent.parent / "Settings" / "prompts.json"


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


def generate_cover_prompt(topic: str, style: str, title: str = "") -> str:
    data = _load_prompts()
    return data["cover_prompt"].format(topic=topic, style=style)


def generate_back_prompt(topic: str) -> str:
    data = _load_prompts()
    return data["back_prompt"].format(topic=topic)