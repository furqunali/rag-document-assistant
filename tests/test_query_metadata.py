import pytest

from query_metadata import build_query_metadata


def test_metadata_normalizes_query():
    assert build_query_metadata("  refund? ",4,0.15,8).question=="refund?"

def test_metadata_rejects_invalid_values():
    with pytest.raises(ValueError): build_query_metadata("",4,0,1)
    with pytest.raises(ValueError): build_query_metadata("x",0,0,1)
    with pytest.raises(ValueError): build_query_metadata("x",1,-1,1)
