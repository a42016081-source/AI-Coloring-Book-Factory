"""Front, back, and full-wrap cover PDFs."""
import io
import logging
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
from PIL import Image

logger = logging.getLogger(__name__)

PAPER_THICKNESS = {"white": 0.002252, "cream": 0.0025}


def _page_size(book_size: str):
    return {
        "8.5x11": (8.5 * inch, 11 * inch),
        "8x10": (8 * inch, 10 * inch),
        "A4": (8.27 * inch, 11.69 * inch),
    }.get(book_size, (8.5 * inch, 11 * inch))


def _draw_centered_text(c, text, x_center, y, font, size, color):
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawCentredString(x_center, y, text)


def _wrap_text(text: str, max_chars: int):
    words = text.split()
    lines, line = [], ""
    for w in words:
        if len(line) + len(w) + 1 > max_chars:
            lines.append(line.strip())
            line = w + " "
        else:
            line += w + " "
    if line.strip():
        lines.append(line.strip())
    return lines


def create_front_cover(title: str, subtitle: str, age_range: str,
                       cover_image_path: str, output_path: str,
                       book_size: str = "8.5x11") -> str:
    w, h = _page_size(book_size)
    c = canvas.Canvas(output_path, pagesize=(w, h))

    # Background
    try:
        img = Image.open(cover_image_path).convert("RGB")
        c.drawImage(ImageReader(img), 0, 0, width=w, height=h, mask="auto")
    except Exception:
        c.setFillColor(HexColor("#f7f7ff"))
        c.rect(0, 0, w, h, fill=1)

    # Title band
    c.setFillColor(HexColor("#FFFFFFCC"))
    c.rect(0.3 * inch, h - 2.2 * inch, w - 0.6 * inch, 1.5 * inch, fill=1, stroke=0)
    _draw_centered_text(c, title, w / 2, h - 1.4 * inch, "Helvetica-Bold", 28,
                        HexColor("#222222"))
    if subtitle:
        _draw_centered_text(c, subtitle, w / 2, h - 1.85 * inch,
                            "Helvetica", 14, HexColor("#444444"))
    _draw_centered_text(c, f"Ages {age_range}", w / 2, 0.9 * inch,
                        "Helvetica-Bold", 16, HexColor("#222222"))
    c.showPage()
    c.save()
    logger.info("Front cover: %s", output_path)
    return output_path


def create_back_cover(description: str, features: list,
                      back_image_path: str, output_path: str,
                      book_size: str = "8.5x11") -> str:
    w, h = _page_size(book_size)
    c = canvas.Canvas(output_path, pagesize=(w, h))

    try:
        img = Image.open(back_image_path).convert("RGB")
        c.drawImage(ImageReader(img), 0, 0, width=w, height=h, mask="auto")
    except Exception:
        c.setFillColor(HexColor("#f0f0f8"))
        c.rect(0, 0, w, h, fill=1)

    c.setFillColor(HexColor("#FFFFFFFF"))
    c.rect(0.4 * inch, 0.4 * inch, w - 0.8 * inch, h - 0.8 * inch, fill=1, stroke=0)

    y = h - 1.0 * inch
    _draw_centered_text(c, "About This Book", w / 2, y, "Helvetica-Bold", 20,
                        HexColor("#222222"))
    y -= 0.5 * inch

    for line in _wrap_text(description, 60)[:20]:
        c.setFont("Helvetica", 12)
        c.setFillColor(HexColor("#333333"))
        c.drawString(0.8 * inch, y, line)
        y -= 0.25 * inch
        if y < 3 * inch:
            break

    y -= 0.3 * inch
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(HexColor("#222222"))
    c.drawString(0.8 * inch, y, "Features:")
    y -= 0.3 * inch
    for feat in features[:8]:
        c.setFont("Helvetica", 11)
        c.drawString(1.0 * inch, y, f"• {feat}")
        y -= 0.22 * inch

    c.showPage()
    c.save()
    logger.info("Back cover: %s", output_path)
    return output_path


def create_full_wrap(front_path: str, back_path: str, page_count: int,
                     output_path: str, book_size: str = "8.5x11",
                     paper: str = "white") -> str:
    """
    Full wrap = back + spine + front.
    Spine width computed from page count & paper thickness (KDP-style).
    """
    pw, ph = _page_size(book_size)
    spine_in = page_count * PAPER_THICKNESS.get(paper, 0.002252) + 0.06
    spine_pt = spine_in * inch
    total_w = pw * 2 + spine_pt
    total_h = ph

    c = canvas.Canvas(output_path, pagesize=(total_w, total_h))

    # Back cover on left
    try:
        back = Image.open(back_path).convert("RGB")
        c.drawImage(ImageReader(back), 0, 0, width=pw, height=ph, mask="auto")
    except Exception:
        pass
    # Spine
    c.setFillColor(HexColor("#222222"))
    c.rect(pw, 0, spine_pt, ph, fill=1, stroke=0)
    c.saveState()
    c.translate(pw + spine_pt / 2, ph / 2)
    c.rotate(-90)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(0, 0, "COLORING BOOK")
    c.restoreState()
    # Front cover on right
    try:
        front = Image.open(front_path).convert("RGB")
        c.drawImage(ImageReader(front), pw + spine_pt, 0,
                    width=pw, height=ph, mask="auto")
    except Exception:
        pass
    # Barcode reserved space (2" x 1.2") bottom-right of back cover
    c.setStrokeColor(HexColor("#CCCCCC"))
    c.setFillColor(HexColor("#FFFFFF"))
    c.rect(0.3 * inch, 0.3 * inch, 2 * inch, 1.2 * inch, fill=1, stroke=1)
    c.setFillColor(HexColor("#888888"))
    c.setFont("Helvetica", 8)
    c.drawCentredString(0.3 * inch + 1 * inch, 0.3 * inch + 0.55 * inch,
                        "BARCODE AREA")

    c.showPage()
    c.save()
    logger.info("Full wrap cover: %s (spine %.3fin)", output_path, spine_in)
    return output_path