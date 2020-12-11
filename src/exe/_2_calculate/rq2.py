
from exe._2_calculate.all import read_pkl


def filter4rq23(df, col, filename):
    df_with = df[(df[col] == True)]
    df_with.drop('results', axis=1).sort_values(by=["id"], ascending=True).to_csv(filename)

def rq2(df):
    print("**どのタイミングでDELETE（RQ2）**********************")
    filter4rq23(df, 'is_deleted_satd', "rq2.csv")
    pass


if __name__ == '__main__':
    df = read_pkl()
    rq2(df)