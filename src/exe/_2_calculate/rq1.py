import pandas
import scipy.stats
import math

from exe._2_calculate.all import read_pkl
from modules.utils import calc_rate

def satdHaveCheck(x):
    if (x.is_added_satd == True) or (x.is_deleted_satd == True):
        return True
    else:
        return False

def accRateTest(df):
    # 検定：比率の差の検定（＝カイ二乗検定）
    crosstab = pandas.crosstab(df['satd_have'], df['is_accepted'])
    x2, p, dof, expected = scipy.stats.chi2_contingency(crosstab)
    print("p-value = " + str(p))
    # 効果量：SQRT(カイ二乗値/N)
    phi = math.sqrt(x2 / len(df))
    print("Effect size = " + str(phi))


def revisionTest(a, b):
    # 検定：U検定
    U, pval = scipy.stats.mannwhitneyu(a, b)
    print("p-value = " + str(pval))
    # 効果量：Z-score / SQRT(N)
    # mannshitneyuではZ-scoreを出してくれないので手動で計算するしかないらしい
    E = (len(a) * len(b)) / 2  # 期待値
    V = math.sqrt(len(a) * len(b) * (len(a) + len(b) + 1) / 12) # 分散
    Z = (U - E) / V  # Z値
    r = math.sqrt(Z ** 2 / (Z ** 2 + len(a) + len(b) - 1))  # r値
    print("Effect size = " + str(r))


def rq1(df):
    print("**RQ1********************")
    #print(df.added_satd.dtype)
    df_with = df[(df.is_added_satd == True) | (df.is_deleted_satd == True)]
    df_without = df[((df.is_added_satd == True) | (df.is_deleted_satd == True)) == False]
    df_with_accepted = df_with['is_accepted']
    df_without_accepted = df_without['is_accepted']
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
    df['satd_have'] = df.apply(lambda x:satdHaveCheck(x), axis=1)
    accRateTest(df)

    print("--Revision-----------------")
    revisionTest(df_with.revisions, df_without.revisions)




if __name__ == '__main__':
    df = read_pkl()
    rq1(df)