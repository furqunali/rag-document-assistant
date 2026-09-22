from ingestion_policy import IngestionFinding
from ingestion_policy_json import to_json


def test_ingestion_policy_json_is_stable():
    findings = (IngestionFinding("DUPLICATES", "error", "2 duplicate documents detected"),)
    assert to_json(findings) == '[{"code":"DUPLICATES","message":"2 duplicate documents detected","severity":"error"}]'
