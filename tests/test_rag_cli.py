from pathlib import Path
from rag_cli import load_chunks

def test_load_chunks_reads_markdown_and_text(tmp_path: Path):
    (tmp_path/"a.md").write_text("Refunds are allowed within 30 days.",encoding="utf-8")
    (tmp_path/"b.txt").write_text("Support is available during business hours.",encoding="utf-8")
    chunks=load_chunks([tmp_path])
    assert len(chunks)==2
    assert {chunk.source for chunk in chunks}=={str(tmp_path/"a.md"),str(tmp_path/"b.txt")}

def test_load_chunks_ignores_other_extensions(tmp_path: Path):
    (tmp_path/"a.csv").write_text("ignored",encoding="utf-8")
    assert load_chunks([tmp_path])==[]
