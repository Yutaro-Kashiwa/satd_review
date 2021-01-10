from exe import PROJECT, CONFIG, CONFIG_DIR, RUN
from modules.SATDReviewExplore import SATDReviewExplore
from modules.review.GerritController import GerritControllerViaLocal
from modules.rq.common import mark_satd
import pandas as pd


def exe(target, project):
    CONFIG.read(CONFIG_DIR / 'projects' / (project + '.ini'))
    PROJECT.update(CONFIG.items('PROJECT'))
    PROJECT["sub_projects"] = PROJECT["sub_projects"].split(",")
    print(PROJECT["sub_projects"])
    PROJECT["bots"] = PROJECT["bots"].split(",")

    gc = GerritControllerViaLocal(PROJECT, target)
    gc.current_review_id = target - 1
    detector = SATDReviewExplore(gc)
    result, error = detector.detect()
    df = pd.DataFrame(result)
    df = mark_satd(df)
    return df, error
