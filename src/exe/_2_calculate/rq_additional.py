import pandas
import scipy.stats
import numpy as np

from sklearn import preprocessing
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression, LinearRegression

from exe._2_calculate.all import read_pkl
from exe._2_calculate.rq1 import rq1


def diff_size_merger(project, df):
    diff = pandas.read_csv(f"inputs/{project}_diff_size.csv")
    diff['id'] = diff['id'].astype(int)
    df['id'] = df['id'].astype(int)
    print("----", project)
    s = set(df['id'].values)
    s = s - set(diff['id'].values)
    print("----")

    df_ = pandas.merge(df, diff, on="id")
    return df_


def get_df(df_, prediction_column):
    # transform 0 or 1
    df_['is_add_or_delete_satd'] = (df_['is_added_satd'] + df_['is_deleted_satd']) >= 1
    df_['is_add_or_delete_satd'] = df_['is_add_or_delete_satd'].astype(int)
    if prediction_column is not None:
        df_[prediction_column] = df_[prediction_column].astype(int)
    return df_


import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler


def decision_tree(df: pandas.DataFrame, prediction_column):
    line_type = 'line'
    # line_type = 'log_line'
    df_ = get_df(df, prediction_column)
    df_[line_type] = scipy.stats.zscore(df_[line_type])
    df_ = df_.loc[:, ['is_added_satd', 'is_deleted_satd', line_type, prediction_column]]

    column_num = len(df_.columns)
    x = df_.iloc[:, 0:(column_num - 1)]
    y = df_.iloc[:, (column_num - 1)]

    model = RandomForestClassifier(max_depth=10, random_state=0)

    model.fit(x, y)
    print(model.feature_importances_)
    pass

def regression(df: pandas.DataFrame, prediction_column):
    line_type = 'line'
    line_type = 'log_line'
    df_ = get_df(df, prediction_column)
    df_[line_type] = scipy.stats.zscore(df_[line_type])
    df_ = df_.loc[:, ['is_add_or_delete_satd', line_type, prediction_column]]

    column_num = len(df_.columns)
    x = df_.iloc[:, 0:(column_num - 1)]
    y = df_.iloc[:, (column_num - 1)]

    if prediction_column == 'is_accepted':
        model = LogisticRegression()
    elif prediction_column == 'revisions':
        model = LinearRegression()
    else:
        raise

    model.fit(x, y)
    print(model.intercept_)
    print(model.coef_)
    print(model.predict([[1, 0]]))
    print(model.predict([[0, 1]]))
    print(model.predict([[0, -1]]))
    print(model.predict([[0, 0]]))
    print(model.predict([[1, 20]]))

from scipy import stats
def correlation(df: pandas.DataFrame):
    # line_type = 'line'
    line_type = 'log_line'
    df_ = get_df(df, None)
    df_[line_type] = scipy.stats.zscore(df_[line_type])
    df_ = df_.loc[:, ['is_add_or_delete_satd', line_type]]
    print(df_.corr())
    a = stats.pointbiserialr(df_.loc[:, line_type], df_.loc[:, 'is_add_or_delete_satd'])
    print(a)


#intervalの範囲でパッチサイズをまとめる．上限はlimitの値．
def splitter(df, interval=200, limit=1000):
    #1.lineでソート(昇順/ascending=Falseで降順)
    df = df.sort_values('line', ascending=True)
    #2. dfを分ける
    min = 1
    max = interval
    while max <= limit:
        # min <= line <= max のものを抽出
        dfn = df[(df['line'] >= min) & (df['line'] <= max)]
        # 必要なら：ランダムに抽出
        # dfn = dfn.sample(n=480, random_state=0)
        yield dfn
        min += interval
        max += interval


import matplotlib.pyplot as plt

# ヒストグラム．累積直線付き．だいたいコピペ
def graph_maker_hist(project, df_input, logging=True):
    df = df_input['line']
    bins = np.linspace(0, 2001, 1001)
    freq = df.value_counts(bins=bins, sort=False)
    # 第2軸用値の算出（この辺コピペ）
    class_value = (bins[:-1] + bins[1:]) / 2  # 階級値
    rel_freq = freq / df.count()  # 相対度数
    cum_freq = freq.cumsum()  # 累積度数
    rel_cum_freq = rel_freq.cumsum()  # 相対累積度数
    dist = pandas.DataFrame(
        {
            "階級値": class_value,
            "度数": freq,
            "相対度数": rel_freq,
            "累積度数": cum_freq,
            "相対累積度数": rel_cum_freq,
        },
        index=freq.index
    )
    fig, ax1 = plt.subplots()
    ax1.set_xlabel("line")
    df.plot(bins=bins, logx=logging, kind='hist')
    ax2 = ax1.twinx()
    ax2.plot(np.arange(len(dist)), dist["相対累積度数"], "-", color="r")
    ax2.set_ylabel("累積相対度数")
    plt.savefig(f"{project}/{project}_line_hist.png")

#lineが一定値以上の変更を抽出してcsvで出す
def extract_big_changes(project, df, threshold=10000):
    df = df.sort_values('line', ascending=True)
    df = df[df['line'] >= threshold]
    # df = df.drop(['is_added_satd', 'is_deleted_satd', 'is_accepted'], axis=1) # 軽くしたいので情報を一部削る
    df = df.drop(['results', 'added_satd', 'deleted_satd'], axis=1)
    df.to_csv(f"{project}/{project}_size_over{threshold}.csv", index=False)


#plot.scatterもやってみる？

def run(project, kubernetes):
    df = read_pkl(project, kubernetes)
    df_ = diff_size_merger(project, df)
    # extract_big_changes(project, df_, 5000)
    # graph_maker_hist(project, df_)
    count = 1
    for dfn in splitter(df_, interval=200, limit=1000):
        print(f"----------------df{count}----------------")
        get_df(dfn, None)
        print(f"line_min:{dfn['line'].min()}, line_max:{dfn['line'].max()}")
        rq1(project, dfn, count)
        # regression(dfn, 'is_accepted')
        # regression(dfn, 'revisions')
        # decision_tree(dfn, 'is_accepted')
        # decision_tree(dfn, 'revisions')
        # correlation(dfn)
        count += 1

if __name__ == '__main__':
    # run("qt", kubernetes=True)
    run("openstack", kubernetes=True)
