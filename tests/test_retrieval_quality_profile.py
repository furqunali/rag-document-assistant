from models import Chunk
from retrieval import Retrieved
from retrieval_quality_profile import profile_retrieval_quality

def r(source,score,index): return Retrieved(Chunk("text",source,index),score)

def test_profiles_scores_and_sources():
    result=profile_retrieval_quality([r("a",.2,0),r("b",.8,1),r("a",.6,2)],threshold=.6)
    assert result.count == 3 and result.distinct_sources == 2
    assert result.mean_score == .533333 and result.threshold_hits == 2

def test_threshold_is_validated():
    try: profile_retrieval_quality([],threshold=1.1)
    except ValueError: pass
    else: raise AssertionError("invalid threshold should fail")
