from models import Chunk
from retrieval import Retrieved
from retrieval_score_profile import profile_scores
import pytest

def test_score_profile_reports_summary_statistics():
    p = profile_scores([Retrieved(Chunk("robot","a.md",0),.8), Retrieved(Chunk("arm","b.md",1),.4), Retrieved(Chunk("hand","c.md",2),.6)])
    assert (p.count, p.minimum, p.maximum, p.mean, p.above_threshold) == (3, .4, .8, .6, 0)

def test_score_profile_counts_threshold_matches():
    results = [Retrieved(Chunk("robot","a.md",0),.8), Retrieved(Chunk("arm","b.md",1),.4), Retrieved(Chunk("hand","c.md",2),.6)]
    assert profile_scores(results, threshold=.6).above_threshold == 2

def test_score_profile_rejects_invalid_threshold():
    with pytest.raises(ValueError, match="threshold"):
        profile_scores([], threshold=1.1)

def test_score_profile_handles_no_results():
    assert profile_scores([]).count == 0
