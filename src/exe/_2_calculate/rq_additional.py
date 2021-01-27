import pandas
import scipy.stats

from sklearn import preprocessing
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression, LinearRegression

from exe._2_calculate.all import read_pkl

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
    if prediction_column is not None:
        df_[prediction_column] = df_[prediction_column].astype(int)
    return df_


import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler


def decision_tree(project, df: pandas.DataFrame, prediction_column):
    line_type = 'line'
    # line_type = 'log_line'
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

def regression(project, df: pandas.DataFrame, prediction_column):
    line_type = 'line'
    line_type = 'log_line'
    df_ = get_df(project, df, prediction_column)
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
def correlation(project, df: pandas.DataFrame):
    # line_type = 'line'
    line_type = 'log_line'
    df_ = get_df(project, df, None)
    df_[line_type] = scipy.stats.zscore(df_[line_type])
    df_ = df_.loc[:, ['is_add_or_delete_satd', line_type]]
    print(df_.corr())
    a = stats.pointbiserialr(df_.loc[:, line_type], df_.loc[:, 'is_add_or_delete_satd'])
    print(a)


def run(project, kubernetes):
    df = read_pkl(project, kubernetes)
    regression(project, df, 'is_accepted')
    regression(project, df, 'revisions')
    decision_tree(project, df, 'is_accepted')
    decision_tree(project, df, 'revisions')
    correlation(project, df)

if __name__ == '__main__':
    run("qt", kubernetes=True)
    # run("openstack", kubernetes=True)
