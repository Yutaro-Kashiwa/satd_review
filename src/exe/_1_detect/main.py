from exe import PROJECT
from modules.SATDReviewExplore import SATDReviewExplore
from modules.review.GerritController import GerritControllerViaLocal

import pandas as pd

from modules.rq.common import mark_satd

if __name__ == '__main__':
    gc = GerritControllerViaLocal(PROJECT, 500)
    # gc.current_review_id = 0
    detector = SATDReviewExplore(gc, workers=10)#Don't assign too large number (10 is recommended)
    result, error = detector.detect()
    df = pd.DataFrame(result)
    df = mark_satd(df)
    df.to_pickle("df.pkl")


    print("**error****************")
    with open("error.csv", mode='w') as f:
        for e in error:
            val = error[e]
            f.write(f'"{e}", "{sorted(val)}"\n')


