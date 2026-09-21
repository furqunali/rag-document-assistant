from pathlib import Path
import pytest
from rag_cli import load_chunks, main

def test_load_chunks_reads_markdown_and_text(tmp_path: Path):
    (tmp_path/"a.md").write_text("Refunds are allowed within 30 days.",encoding="utf-8")
    (tmp_path/"b.txt").write_text("Support is available during business hours.",encoding="utf-8")
    chunks=load_chunks([tmp_path])
    assert len(chunks)==2
    assert {chunk.source for chunk in chunks}=={str(tmp_path/"a.md"),str(tmp_path/"b.txt")}

def test_load_chunks_ignores_other_extensions(tmp_path: Path):
    (tmp_path/"a.csv").write_text("ignored",encoding="utf-8")
    assert load_chunks([tmp_path])==[]

def test_main_rejects_non_finite_or_out_of_range_threshold(tmp_path: Path, monkeypatch):
    doc=tmp_path/"doc.md"
    doc.write_text("Refunds are allowed within 30 days.",encoding="utf-8")
    for value in ("nan", "inf", "-inf", "-0.1", "1.1"):
        monkeypatch.setattr("sys.argv", ["rag_cli", "refunds", str(doc), f"--threshold={value}"])
        with pytest.raises(SystemExit, match="--threshold"):
            main()


def test_load_chunks_reports_unreadable_text(tmp_path: Path):
    path = tmp_path / "broken.txt"
    path.write_bytes(b"\\xff\\xfe\\xfa")
    with pytest.raises(ValueError, match="unable to read document"):
        load_chunks([path])
