import pandas

from exe._2_calculate.all import read_pkl
from exe._2_calculate.rq2 import filter_by_column, write, is_revised


def rq3(project, df):
    print("**ADD timing (RQ3)**********************")
    df = filter_by_column(df, 'is_added_satd', f"{project}/{project}_rq3.csv")
    df['is_revised'] = df.apply(lambda x: is_revised(x, 'added_satd'), axis=1)
    all = len(df)
    revised = len(df[df.is_revised])
    write(all, revised, f"{project}/{project}_statistics_add_timing.csv")

