
import pandas as pd

from exe._2_calculate import rq2, rq1
from exe._2_calculate import discussion1


def read_pkl(project, kube=False):
    if kube:
        return pd.read_pickle(f"../distribution_util/{project}/{project}_df.pkl")
    return pd.read_pickle(f"../_1_detect/{project}_df.pkl")


def run(project, kubernetes):
    print(project)
    df = read_pkl(project, kubernetes)
    # rq1.run(project, df)
    # rq1.run2(project, df)
    rq2.run(project, df)
    # discussion1.run(project, df, exclude_one_time_accepted=True)
    # print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
    discussion1.run(project, df, exclude_one_time_accepted=False)


if __name__ == '__main__':
    run("qt", kubernetes=True)
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    run("openstack", kubernetes=True)





