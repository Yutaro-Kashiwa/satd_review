import pandas

from exe._2_calculate.all import read_pkl
from exe._2_calculate.rq2 import filter4rq23, output4rq23


def revisedChecker4rq3(x):
    dic = x.added_satd
    for v in dic.values():
        if v >= 2:
            return True
    return False

def rq3(project, df):
    print("**どのタイミングでADD（RQ3）**********************")
    df = filter4rq23(df, 'is_added_satd', f"{project}/{project}_rq3.csv")
    df['is_revised'] = df.apply(lambda x: revisedChecker4rq3(x), axis=1)
    all = len(df)
    revised = len(df[df.is_revised])
    output4rq23(all, revised, f"{project}/{project}_statistics_add_timing.csv")


if __name__ == '__main__':
    import pandas as pd
    df = read_pkl()
    rq3(df)