from models import Chunk
from retrieval import Retrieved
from retrieval_score_spread import score_spread

def test_score_spread_returns_range():
    results = [Retrieved(Chunk("a","a.md",0),.2), Retrieved(Chunk("b","b.md",1),.8)]
    assert score_spread(results) == .6

def test_score_spread_handles_equal_scores():
    results = [Retrieved(Chunk("a","a.md",0),.5), Retrieved(Chunk("b","b.md",1),.5)]
    assert score_spread(results) == 0.0

def test_score_spread_handles_empty_results():
    assert score_spread([]) == 0.0
