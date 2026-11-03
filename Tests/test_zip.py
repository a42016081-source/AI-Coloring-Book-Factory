import os
import tempfile
from pathlib import Path


def test_zip_creation():
    from Utils.zip_creator import create_book_zip
    with tempfile.TemporaryDirectory() as d:
        ws = Path(d) / "book"
        (ws / "Images").mkdir(parents=True)
        (ws / "Interior.pdf").write_bytes(b"%PDF-1.4 test")
        (ws / "Images" / "Page_001.png").write_bytes(b"\x89PNG test")
        out = Path(d) / "book.zip"
        create_book_zip(ws, out)
        assert out.exists()
        import zipfile
        with zipfile.ZipFile(out) as zf:
            names = zf.namelist()
            assert any("Interior.pdf" in n for n in names)
            assert any("Page_001.png" in n for n in names)