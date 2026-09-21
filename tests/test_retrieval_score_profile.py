from models import Chunk
from retrieval import Retrieved
from retrieval_score_profile import profile_scores

def test_score_profile_reports_summary_statistics():
    p = profile_scores([Retrieved(Chunk("robot","a.md",0),.8), Retrieved(Chunk("arm","b.md",1),.4), Retrieved(Chunk("hand","c.md",2),.6)])
    assert (p.count, p.minimum, p.maximum, p.mean) == (3, .4, .8, .6)

def test_score_profile_handles_no_results():
    assert profile_scores([]).count == 0
