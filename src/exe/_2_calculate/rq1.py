import pandas

from exe._2_calculate.all import read_pkl
from modules.utils import calc_rate


def rq1(df):
    print("**RQ1********************")
    df_with = df[(df.added_satd == True) | (df.deleted_satd == True)]
    df_without = df[((df.added_satd == True) | (df.deleted_satd == True)) == False]
    df_with_accepted = df_with[df_with.is_accepted]
    df_without_accepted = df_without[df_without.is_accepted]
    print("--Statistics-----------------")
    header = ['', "SATD", "non-SATD"]
    num = ['num', len(df_with), (len(df_without))]
    accepted_num = 'accepted_num', len(df_with_accepted), (len(df_without_accepted))
    accepted_rate = ['accepted_rate', calc_rate(len(df_with_accepted), len(df_with)),
                     calc_rate(len(df_without_accepted), len(df_without))]
    min_revisions = ['min_revisions', df_with['revisions'].min(), df_without['revisions'].min()]
    mean_revisions = ['mean_revisions', df_with['revisions'].mean(), df_without['revisions'].mean()]
    median_revisions = ['median_revisions', df_with['revisions'].median(), df_without['revisions'].median()]
    max_revisions = ['max_revisions', df_with['revisions'].max(), df_without['revisions'].max()]
    out_df = pandas.DataFrame([num, accepted_num, accepted_rate, min_revisions, mean_revisions, median_revisions, max_revisions], columns=header)
    out_df.to_csv("statistics.csv")

    print("--Acceptance Rate-----------------")
    #TODO: df_with_accepted（SATD付き採択されたレビュー）とdf_without_accepted（SATDなし採択されたレビュー）を使って検定＋効果量測定

    print("--Revision-----------------")
    #TODO: df_with（SATD付きレビュー）とdf_without_accepted（SATDなしレビュー）を使って検定＋効果量測定



if __name__ == '__main__':
    df = read_pkl("")
    rq1(df)