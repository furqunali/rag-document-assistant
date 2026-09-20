from ingestion_policy import IngestionFinding
from ingestion_summary import summarize_ingestion

def test_ingestion_summary_counts_findings():
    findings = (IngestionFinding("DUPLICATES", "error", "duplicates"), IngestionFinding("EMPTY_INGESTION", "warning", "empty"))
    summary = summarize_ingestion(findings)
    assert summary.total == 2
    assert summary.errors == 1
    assert summary.warnings == 1
    assert summary.infos == 0
    assert not summary.healthy
