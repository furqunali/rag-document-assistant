from ingestion_policy import IngestionFinding
from ingestion_summary import summarize_ingestion

def test_ingestion_summary_counts_findings():
    findings = (IngestionFinding("DUPLICATES", "error", "duplicates"), IngestionFinding("EMPTY_INGESTION", "warning", "empty"))
    assert summarize_ingestion(findings) == (2, 1, 1, 0, False)
