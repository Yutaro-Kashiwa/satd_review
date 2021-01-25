import os

from exe import PROJECT, ENV, load_project
from modules.SATDReviewExplore import SATDReviewExplore
from modules.review.GerritController import GerritControllerViaLocal

import pandas as pd

from modules.rq.common import mark_satd

def write(df, error, file_dir):
    # output
    os.makedirs(file_dir, exist_ok=True)
    df.to_pickle(file_dir + "/df.pkl")
    # err
    os.makedirs(file_dir, exist_ok=True)

    with open(file_dir + "/error.csv", mode='w') as f:
        for e in error:
            val = error[e]
            f.write(f'"{e}", "{sorted(val)}"\n')

def run(project, start, stop, workers=10):
    gc = GerritControllerViaLocal(project, stop)
    gc.current_review_id = start
    detector = SATDReviewExplore(gc, workers=workers)  # Don't assign too large number (10 is recommended)
    result, error = detector.detect()
    df = pd.DataFrame(result)
    df = mark_satd(df)

    return df, error


import sys
if __name__ == '__main__':
    args = sys.argv
    if len(args) == 5:
        project = load_project(args[1])
        start = int(args[2])
        stop = int(args[3])
        workers = int(args[4])
        df, error = run(project, start, stop, workers)
    else:
        df, error = run(PROJECT, 0, int(PROJECT['last_review_no']), workers=10)
    file_dir = f"{ENV['out_dir']}/{project['name']}/{start}-{stop}"
    write(df, error, file_dir)


