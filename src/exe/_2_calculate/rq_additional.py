import pandas
import scipy.stats
import numpy as np

from sklearn import preprocessing
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression, LinearRegression

from exe._2_calculate.all import read_pkl

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

#input->df, output->df*3
def spliter(df):
    #1.lineでソート(昇順)
    df = df.sort_values('line')
    #2.3分割
    df1, df2, df3 = np.array_split(df, 3)
    return df1, df2, df3

def run(project, kubernetes):
    df = read_pkl(project, kubernetes)
    #get_dfを前半と後半に分けましょう
    df_ = diff_size_merger(project, df)
    df1, df2, df3 = spliter(df_)
    count = 1
    for dfn in (df1, df2, df3):
        print(f"----------------df{count}----------------")
        regression(dfn, 'is_accepted')
        regression(dfn, 'revisions')
        decision_tree(dfn, 'is_accepted')
        decision_tree(dfn, 'revisions')
        correlation(dfn)
        count += 1

if __name__ == '__main__':
    run("qt", kubernetes=True)
    # run("openstack", kubernetes=True)
