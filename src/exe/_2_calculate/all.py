
import pandas as pd

def read_pkl(project):
    # return pd.read_pickle(f"../_1_detect/{project}_df.pkl")
    return pd.read_pickle(f"../distribution_util/{project}/{project}_df.pkl")





if __name__ == '__main__':
    project = "qt"
    project = "openstack"
    from exe._2_calculate.rq1 import rq1
    from exe._2_calculate.rq2 import rq2
    from exe._2_calculate.rq3 import rq3
    df = read_pkl(project)
    rq1(project, df)
    rq2(project, df)
    rq3(project, df)




