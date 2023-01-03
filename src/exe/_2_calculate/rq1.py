import pandas
import scipy.stats
import math
import seaborn as sns

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

from modules.utils import calc_rate

def is_in_revised(x, col):
    dic = x[col]
    for val in dic.values():
        if val >= 2:
            return True
    return False

def accept_rate_ss(project, a, b, c, d, other=""):
    # 検定：比率の差の検定（＝カイ二乗検定）
    crosstab = pandas.DataFrame([[a, b], [c, d]])
    x2, p, dof, expected = scipy.stats.chi2_contingency(crosstab)
    print(f"p-value({other}) = {p}")

    accepted_header = ['--Acceptance Rate-----------------', '', '']
    accepted_p = ['p-value', '', p]
    # 効果量：SQRT(カイ二乗値/N) # NOTE: effect size should not be calculated for rates
    # phi = math.sqrt(x2 / (a+b+c+d))
    # print("Effect size = " + str(phi))
    # accepted_eff = ['effect_size', '', phi]
    out_df = pandas.DataFrame([accepted_header, accepted_p])  # accepted_eff
    out_df.to_csv(f"{project}/{project}_acc{other}_statistics.csv", mode='w', header=False)


def revision_ss(project, a, b):
    # 検定：U検定
    U, p = scipy.stats.mannwhitneyu(a, b)
    print("p-value = " + str(p))
    # 効果量：Z-score / SQRT(N)
    # mannshitneyuではZ-scoreを出してくれないので手動で計算するしかないらしい
    E = (len(a) * len(b)) / 2  # 期待値
    V = math.sqrt(len(a) * len(b) * (len(a) + len(b) + 1) / 12)  # 分散
    Z = (U - E) / V  # Z値
    r = math.sqrt(Z ** 2 / (Z ** 2 + len(a) + len(b) - 1))  # r値
    print("Effect size = " + str(r))
    revision_header = ['--Revision-----------------', '', '']
    revision_p = ['p-value', '', p]
    revision_eff = ['effect_size', '', r]
    out_df = pandas.DataFrame([revision_header, revision_p, revision_eff])
    out_df.to_csv(f"{project}/{project}_rev_statistics.csv", mode='w', header=False)

def run2(project, df):
    d = df[(df['is_added_satd'] == True)].sort_values(by=["id"], ascending=True)
    df['is_in_revised'] = df.apply(lambda x: is_in_revised(x, 'added_satd'), axis=1)
    df_revised = df[df.is_in_revised == True]
    df_first = df[df.is_in_revised == False]
    df_revised_accepted = df_revised[df_revised.is_accepted]
    df_first_accepted = df_first[df_first.is_accepted]
    print("--Statistics-----------------")
    header = ['', "Revised patches", "First patch"]
    num = ['num', len(df_revised), (len(df_first))]
    accepted_num = 'accepted_num', len(df_revised_accepted), (len(df_first_accepted))
    accepted_rate = ['accepted_rate', calc_rate(len(df_revised_accepted), len(df_revised)),
                     calc_rate(len(df_first_accepted), len(df_first))]
    min_revisions = ['min_revisions', df_revised['revisions'].min(), df_first['revisions'].min()]
    mean_revisions = ['mean_revisions', df_revised['revisions'].mean(), df_first['revisions'].mean()]
    median_revisions = ['median_revisions', df_revised['revisions'].median(), df_first['revisions'].median()]
    max_revisions = ['max_revisions', df_revised['revisions'].max(), df_first['revisions'].max()]
    out_df = pandas.DataFrame(
        [num, accepted_num, accepted_rate, min_revisions, mean_revisions, median_revisions, max_revisions],
        columns=header)
    out_df.to_csv(f"{project}/{project}_revises_statistics.csv")
    print("--Acceptance Rate-----------------")
    a, b, c, d = len(df_revised_accepted), len(df_revised) - len(df_revised_accepted), \
                 len(df_first_accepted), len(df_first) - len(df_first_accepted)
    accept_rate_ss(project, a, b, c, d, other="_revised")


def run(project, df):
    plot_revisions(project, df)
    print("**RQ1********************")
    df_with = df[df.is_added_satd == True]#is_added_satd,is_deleted_satd
    df_without = df[df.is_added_satd == False]
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
    out_df = pandas.DataFrame(
        [num, accepted_num, accepted_rate, min_revisions, mean_revisions, median_revisions, max_revisions],
        columns=header)
    out_df.to_csv(f"{project}/{project}_statistics.csv")


    print("--Acceptance Rate-----------------")
    a, b, c, d = len(df_with_accepted), len(df_with) - len(df_with_accepted), \
                 len(df_without_accepted), len(df_without) - len(df_without_accepted)
    accept_rate_ss(project, a, b, c, d)

    print("--Revision-----------------")
    revision_ss(project, df_with.revisions, df_without.revisions)




def plot_revisions(project, df):
    tp="revisions"
    sns.boxplot(x=df["is_added_satd"], y=df[tp])
    plt.yscale('log')
    plt.ylim([0,1000])
    plt.savefig(f'{project}_{tp}.png')
    plt.close()

