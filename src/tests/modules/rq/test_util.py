from exe import PROJECT
from modules.SATDReviewExplore import SATDReviewExplore
from modules.review.GerritController import GerritControllerViaLocal
from modules.rq.common import mark_satd
import pandas as pd

def exe(target):
    gc = GerritControllerViaLocal(PROJECT, target)
    gc.current_review_id = target - 1
    detector = SATDReviewExplore(gc)
    result, error = detector.detect()
    df = pd.DataFrame(result)
    df = mark_satd(df)
    return df