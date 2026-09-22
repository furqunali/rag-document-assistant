from document_loader_expanded import load_document
from ingestion_health import assess_documents
from ingestion_policy import evaluate_ingestion


def test_ingestion_policy_reports_duplicates():
    health = assess_documents([load_document("a", "same"), load_document("b", "same")])
    assert evaluate_ingestion(health)[0].code == "DUPLICATES"

def test_ingestion_policy_reports_empty_input():
    health = assess_documents([])
    assert evaluate_ingestion(health)[0].code == "EMPTY_INGESTION"
