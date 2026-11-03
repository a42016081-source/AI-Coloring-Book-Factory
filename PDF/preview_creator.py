"""Small preview PDF — first 3 pages + cover."""
import logging
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image

logger = logging.getLogger(__name__)


def create_preview(image_paths, cover_path, output_path, title="Preview"):
    # 2x2 grid on a single letter page
    pw, ph = letter
    c = canvas.Canvas(output_path, pagesize=(pw, ph))
    c.setTitle(title)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(pw / 2, ph - 0.5 * 36, title)

    thumbs = []
    if cover_path:
        thumbs.append(cover_path)
    thumbs.extend(image_paths[:3])
    thumbs = thumbs[:4]

    margin = 0.5 * 36
    cell_w = (pw - 3 * margin) / 2
    cell_h = (ph - 2 * 36 - 3 * margin) / 2
    positions = [
        (margin, ph - 36 - margin - cell_h),
        (margin + cell_w + margin, ph - 36 - margin - cell_h),
        (margin, ph - 36 - margin - cell_h - margin - cell_h),
        (margin + cell_w + margin, ph - 36 - margin - cell_h - margin - cell_h),
    ]
    for path, (x, y) in zip(thumbs, positions):
        try:
            img = Image.open(path).convert("RGB")
            iw, ih = img.size
            scale = min(cell_w / iw, cell_h / ih)
            w2, h2 = iw * scale, ih * scale
            c.drawImage(ImageReader(img), x, y, width=w2, height=h2, mask="auto")
        except Exception as e:
            logger.warning("Preview: cannot draw %s: %s", path, e)
    c.showPage()
    c.save()
    logger.info("Preview PDF: %s", output_path)
    return output_path