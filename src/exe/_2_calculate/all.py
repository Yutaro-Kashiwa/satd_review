
import pandas as pd

def read_pkl():
    return pd.read_pickle("../_1_detect/df.pkl")





if __name__ == '__main__':
    from exe._2_calculate.rq1 import rq1
    from exe._2_calculate.rq2 import rq2
    from exe._2_calculate.rq3 import rq3
    df = read_pkl()
    rq1(df)
    rq2(df)
    rq3(df)




