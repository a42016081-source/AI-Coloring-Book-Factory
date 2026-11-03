"""Create the interior coloring book PDF."""
import io
import logging
from pathlib import Path
from typing import List
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from PIL import Image

logger = logging.getLogger(__name__)

PAGE_SIZES = {
    "8.5x11": (8.5 * inch, 11 * inch),
    "8x10": (8 * inch, 10 * inch),
    "A4": (8.27 * inch, 11.69 * inch),
    "letter": letter,
}


def _page_size(book_size: str):
    return PAGE_SIZES.get(book_size, PAGE_SIZES["8.5x11"])


def _fit_image_on_canvas(c: canvas.Canvas, img: Image.Image,
                        page_w: float, page_h: float, margin: float = 0.4 * inch):
    avail_w = page_w - 2 * margin
    avail_h = page_h - 2 * margin
    iw, ih = img.size
    scale = min(avail_w / iw, avail_h / ih)
    new_w, new_h = iw * scale, ih * scale
    x = (page_w - new_w) / 2
    y = (page_h - new_h) / 2
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    from reportlab.lib.utils import ImageReader
    c.drawImage(ImageReader(buf), x, y, width=new_w, height=new_h, mask="auto")


def create_interior_pdf(image_paths: List[str], output_path: str,
                        book_size: str = "8.5x11", title: str = "") -> str:
    page_w, page_h = _page_size(book_size)
    c = canvas.Canvas(output_path, pagesize=(page_w, page_h))
    c.setTitle(title or "Coloring Book Interior")
    for path in image_paths:
        try:
            img = Image.open(path).convert("L")
            _fit_image_on_canvas(c, img, page_w, page_h)
            c.showPage()
        except Exception as e:
            logger.error("Failed to add page %s: %s", path, e)
    c.save()
    logger.info("Interior PDF created: %s", output_path)
    return output_path