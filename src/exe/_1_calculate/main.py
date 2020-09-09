from exe import PROJECT, ENV
from modules.SATDReviewExplore import SATDReviewExplore
from modules.review.GerritController import GerritControllerViaLocal

import pandas as pd

from modules.rq.common import mark_satd, count_satd

if __name__ == '__main__':
    gc = GerritControllerViaLocal(PROJECT, ENV['data_dir'])
    # gc.current_review_id = 7006
    detector = SATDReviewExplore(gc)
    result, error = detector.detect()
    df = pd.DataFrame(result)
    df = mark_satd(df)

    print("**SATDの数（RQ0）**********************")
    df_with = df[(df.added_satd == True) | (df.deleted_satd == True)]
    df_without = df[((df.added_satd == True) | (df.deleted_satd == True)) == False]
    print(len(df_with), (len(df_without)))
    print("**アクセプタンスRate（RQ1）**********************")
    df_with_accepted = df_with[df_with.is_accepted]
    df_without_accepted = df_without[df_without.is_accepted]
    print(len(df_with_accepted) / len(df_with), (len(df_without_accepted) / len(df_without)))

    print("**リビジョン（RQ1）**********************")
    print('min', df_with['revisions'].min(), df_without['revisions'].min())
    print('mean', df_with['revisions'].mean(), df_without['revisions'].mean())
    print('median', df_with['revisions'].median(), df_without['revisions'].median())
    print('max', df_with['revisions'].max(), df_without['revisions'].max())

    print("**どのタイミングでDELETE（RQ2）**********************")
    # リビジョンの最初 or 途中？

    print("**どのタイミングでADD（RQ3）**********************")

    print("**Additional リビジョンの途中で追加と最初に追加でAcceptance rate**********************")

    print("error", error)
