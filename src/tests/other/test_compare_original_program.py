import pandas as pd

def check(a, b):
    for r in a:
        if r in b:
            pass
        else:
            print(r + " is found")
            raise

if __name__ == '__main__':
    ans = pd.read_csv("addDelChecker_openstack.csv")
    ans_rq2 = list(ans[ans['Del_include?']==1]['NUMBER'])
    ans_rq3 = list(ans[ans['Add_include?']==1]['NUMBER'])

    rq2 = list(pd.read_csv("../../exe/_2_calculate/rq2.csv")["id"])
    check(rq2, ans_rq2)
    # check(ans_rq2, rq2)
    rq3 = list(pd.read_csv("../../exe/_2_calculate/rq3.csv")["id"])
    check(rq3, ans_rq3)
    # check(ans_rq3, rq3)