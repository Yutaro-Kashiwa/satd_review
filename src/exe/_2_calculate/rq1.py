import pandas
import scipy.stats
import math

from exe._2_calculate.all import read_pkl
from modules.utils import calc_rate


def accRateTest(project, a, b, c, d):
    # 検定：比率の差の検定（＝カイ二乗検定）
    crosstab = pandas.DataFrame([[a, b], [c, d]])
    x2, p, dof, expected = scipy.stats.chi2_contingency(crosstab)
    print("p-value = " + str(p))
    # 効果量：SQRT(カイ二乗値/N)
    phi = math.sqrt(x2 / (a+b+c+d))
    print("Effect size = " + str(phi))
    accepted_header = ['--Acceptance Rate-----------------', '', '']
    accepted_p = ['p-value', '', p]
    accepted_eff = ['effect_size', '', phi]
    out_df = pandas.DataFrame([accepted_header, accepted_p, accepted_eff])
    out_df.to_csv(f"{project}/{project}_acc_statistics.csv", mode='a', header=False)


def revisionTest(project, a, b):
    # 検定：U検定
    U, p = scipy.stats.mannwhitneyu(a, b)
    print("p-value = " + str(p))
    # 効果量：Z-score / SQRT(N)
    # mannshitneyuではZ-scoreを出してくれないので手動で計算するしかないらしい
    E = (len(a) * len(b)) / 2  # 期待値
    V = math.sqrt(len(a) * len(b) * (len(a) + len(b) + 1) / 12) # 分散
    Z = (U - E) / V  # Z値
    r = math.sqrt(Z ** 2 / (Z ** 2 + len(a) + len(b) - 1))  # r値
    print("Effect size = " + str(r))
    revision_header = ['--Revision-----------------', '', '']
    revision_p = ['p-value', '', p]
    revision_eff = ['effect_size', '', r]
    out_df = pandas.DataFrame([revision_header, revision_p, revision_eff])
    out_df.to_csv(f"{project}/{project}_rev_statistics.csv", mode='a', header=False)


def rq1(project, df):
    print("**RQ1********************")
    df_with = df[(df.is_added_satd == True) | (df.is_deleted_satd == True)]
    df_without = df[((df.is_added_satd == True) | (df.is_deleted_satd == True)) == False]
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
    out_df.to_csv(f"{project}/{project}_statistics.csv")

    print("--Acceptance Rate-----------------")
    a, b, c, d = len(df_with_accepted), len(df_with) - len(df_with_accepted), \
                 len(df_without_accepted), len(df_without) - len(df_without_accepted)
    accRateTest(project, a, b, c, d)

    print("--Revision-----------------")
    revisionTest(project, df_with.revisions, df_without.revisions)





project = "qt"
if __name__ == '__main__':
    df = read_pkl()
    rq1(project, df)