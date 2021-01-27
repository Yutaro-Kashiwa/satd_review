import pandas
import scipy.stats
import math

from sklearn import preprocessing
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression, LinearRegression

from exe._2_calculate.all import read_pkl
from modules.utils import calc_rate


def accept_rate_ss(project, a, b, c, d):
    # 検定：比率の差の検定（＝カイ二乗検定）
    crosstab = pandas.DataFrame([[a, b], [c, d]])
    x2, p, dof, expected = scipy.stats.chi2_contingency(crosstab)
    print("p-value = " + str(p))

    accepted_header = ['--Acceptance Rate-----------------', '', '']
    accepted_p = ['p-value', '', p]
    # 効果量：SQRT(カイ二乗値/N) # NOTE: effect size should not be calculated for rates
    # phi = math.sqrt(x2 / (a+b+c+d))
    # print("Effect size = " + str(phi))
    # accepted_eff = ['effect_size', '', phi]
    out_df = pandas.DataFrame([accepted_header, accepted_p])  # accepted_eff
    out_df.to_csv(f"{project}/{project}_acc_statistics.csv", mode='w', header=False)


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


def get_df(project, df, prediction_column):
    diff = pandas.read_csv(f"inputs/{project}_diff_size.csv")
    diff['id'] = diff['id'].astype(int)
    df['id'] = df['id'].astype(int)
    print("----", project)
    s = set(df['id'].values)
    s = s - set(diff['id'].values)
    print("----")

    df_ = pandas.merge(df, diff, on="id")
    # transform 0 or 1
    df_['is_add_or_delete_satd'] = (df_['is_added_satd'] + df_['is_deleted_satd']) >= 1
    df_['is_add_or_delete_satd'] = df_['is_add_or_delete_satd'].astype(int)
    df_[prediction_column] = df_[prediction_column].astype(int)
    return df_


import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler


def regression(project, df: pandas.DataFrame, prediction_column):
    line_type = 'line'
    line_type = 'log_line'
    df_ = get_df(project, df, prediction_column)
    df_[line_type] = scipy.stats.zscore(df_[line_type])
    df_ = df_.loc[:, ['is_added_satd', 'is_deleted_satd', line_type, prediction_column]]

    column_num = len(df_.columns)
    x = df_.iloc[:, 0:(column_num - 1)]
    y = df_.iloc[:, (column_num - 1)]

    model = RandomForestClassifier(max_depth=10, random_state=0)

    model.fit(x, y)
    print(model.feature_importances_)
    pass


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

    regression(project, df, 'is_accepted')
    regression(project, df, 'revisions')
