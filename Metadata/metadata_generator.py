"""Generate KDP-ready metadata + website listing."""
import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


def build_metadata(topic: str, title: str, page_count: int,
                   age_range: str, book_size: str, style: str,
                   language: str = "English") -> Dict[str, str]:
    subtitle = f"{page_count} Fun & Easy {topic} Coloring Pages for Kids Ages {age_range}"
    description = (
        f"Welcome to a world of creativity with {title}!\n\n"
        f"This coloring book features {page_count} original {topic.lower()} illustrations "
        f"designed with clean, bold outlines that make coloring easy and fun for young artists. "
        f"Each page is printed single-sided so colors never bleed through — perfect for crayons, "
        f"colored pencils, or markers.\n\n"
        f"Inside this book:\n"
        f"• {page_count} unique coloring pages\n"
        f"• Large {book_size} inch pages\n"
        f"• Thick, clean black outlines\n"
        f"• Single-sided printing\n"
        f"• Perfect for ages {age_range}\n\n"
        f"Whether you're a parent looking for a screen-free activity or a child discovering the joy "
        f"of coloring, this {topic.lower()} coloring book provides hours of imaginative fun.\n\n"
        f"Grab your crayons and let the creativity begin!"
    )

    keywords = [
        f"{topic} coloring book",
        f"{topic} coloring book for kids",
        f"coloring book for kids ages {age_range}",
        f"easy coloring pages for toddlers",
        f"{topic.lower()} activity book",
        f"childrens {topic.lower()} coloring",
        f"coloring book for beginners",
    ]

    categories = [
        "Juvenile Nonfiction > Activity Books > Coloring",
        f"Children's Books > Animals",
        "Crafts & Hobbies > Coloring Books",
    ]

    features = [
        f"{page_count} unique illustrations",
        f"Large {book_size}-inch pages",
        "Single-sided pages",
        "Thick black outlines",
        f"For ages {age_range}",
    ]

    website_listing = (
        f"🎨 {title} — {page_count} Beautiful {topic} Coloring Pages\n\n"
        f"Perfect for kids ages {age_range}. Each page features a unique, "
        f"hand-crafted-style {topic.lower()} illustration ready to color. "
        f"Instant digital download, print at home, unlimited use.\n\n"
        f"✅ {page_count} pages\n"
        f"✅ {book_size} format\n"
        f"✅ Print-ready PDF\n"
        f"✅ Instant download\n"
    )

    publishing_info = (
        f"Title: {title}\n"
        f"Subtitle: {subtitle}\n"
        f"Page Count (interior): {page_count}\n"
        f"Trim Size: {book_size}\n"
        f"Language: {language}\n"
        f"Category: Coloring Book\n"
        f"Age Range: {age_range}\n\n"
        "Copyright © All rights reserved. This book is for personal use only. "
        "Reproduction of any part without written permission is prohibited.\n\n"
        "Note: This book contains no ISBN and no registered barcode. "
        "Publisher should register ISBN with their local authority before publishing."
    )

    return {
        "Title.txt": title,
        "Subtitle.txt": subtitle,
        "Description.txt": description,
        "Keywords.txt": "\n".join(keywords),
        "Categories.txt": "\n".join(categories),
        "Publishing_Info.txt": publishing_info,
        "Website_Listing.txt": website_listing,
        "_features": features,  # internal, not written
    }


def write_metadata_files(metadata: Dict[str, str], out_dir: str) -> List[str]:
    p = Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    written = []
    for name, content in metadata.items():
        if name.startswith("_"):
            continue
        f = p / name
        f.write_text(str(content), encoding="utf-8")
        written.append(str(f))
    return written