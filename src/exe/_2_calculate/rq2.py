import pandas

from exe._2_calculate.all import read_pkl
from modules.utils import calc_rate


def filter_by_column(df, col, filename):
    df_with = df[(df[col] == True)]
    df_with = df_with.drop('results', axis=1).sort_values(by=["id"], ascending=True)
    df_with.to_csv(filename)
    return df_with


def is_revised(x, col):
    dic = x[col]
    for v in dic.values():
        if v >= 2:
            return True
    return False


def write(all, revised, filename):
    initial = all - revised
    header = ['', 'revised', 'initial']
    num = ['num', revised, initial]
    rate = ['rate', calc_rate(revised, all), calc_rate(initial, all)]
    out_df = pandas.DataFrame([num, rate], columns=header)
    out_df.to_csv(filename)


def rq2(project, df):
    print("**DELETE timing(RQ2)**********************")
    df = filter_by_column(df, 'is_deleted_satd', f"{project}/{project}_rq2.csv")
    df['is_revised'] = df.apply(lambda x: is_revised(x), axis=1)
    all = len(df)
    revised = len(df[df.is_revised])
    write(all, revised, f"{project}/{project}_statistics_delete_timing.csv")


