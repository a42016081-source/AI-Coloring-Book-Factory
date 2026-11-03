import os
import tempfile
from PIL import Image


def _make_test_image(path, size=(400, 500)):
    img = Image.new("L", size, 255)
    img.save(path)
    return path


def test_interior_pdf_creates():
    from PDF.pdf_creator import create_interior_pdf
    with tempfile.TemporaryDirectory() as d:
        paths = []
        for i in range(3):
            p = os.path.join(d, f"p{i}.png")
            _make_test_image(p)
            paths.append(p)
        out = os.path.join(d, "interior.pdf")
        create_interior_pdf(paths, out, "8.5x11", "Test")
        assert os.path.exists(out)
        assert os.path.getsize(out) > 500


def test_cover_pdf_creates():
    from PDF.cover_creator import create_front_cover
    with tempfile.TemporaryDirectory() as d:
        img = os.path.join(d, "cover.png")
        _make_test_image(img, (600, 800))
        out = os.path.join(d, "front.pdf")
        create_front_cover("Title", "Sub", "4-8", img, out, "8.5x11")
        assert os.path.exists(out)