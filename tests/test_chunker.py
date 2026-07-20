import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.chunker import hash_content, chunk_document

def test_same_content_gives_same_hash():
    assert hash_content("Hello world") == hash_content("Hello world")

def test_different_content_gives_different_hash():
    assert hash_content("Hello world") != hash_content("Hello there")

def test_whitespace_differences_dont_change_hash():
    # extra spaces/newlines shouldn't count as a "real" change
    assert hash_content("Hello   world") == hash_content("Hello world")
    assert hash_content("Hello\nworld") == hash_content("Hello world")

def test_chunk_document_splits_on_paragraphs(tmp_path):
    doc = tmp_path / "sample.md"
    doc.write_text("Paragraph one.\n\nParagraph two.\n\nParagraph three.")

    chunks = chunk_document(doc)

    assert len(chunks) == 3
    assert chunks[0].chunk_id == "sample.md#0"
    assert chunks[1].content == "Paragraph two."