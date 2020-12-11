
from exe._2_calculate.all import read_pkl
from exe._2_calculate.rq2 import filter4rq23


def rq3(df):
    print("**どのタイミングでADD（RQ3）**********************")
    filter4rq23(df, 'is_added_satd', "rq3.csv")
    pass


if __name__ == '__main__':
    import pandas as pd
    df = read_pkl()
    rq3(df)