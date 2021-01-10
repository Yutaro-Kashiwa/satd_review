import pandas as pd

def check(checkee, checker, check_ranges=None):
    for r in checkee:
        if not (check_ranges is None) and (r not in check_ranges):
            continue
        if r in checker:
            pass
        else:
            print("  !!" + str(r) + " is not in checker")
            # raise

if __name__ == '__main__':
    check_ranges = range(0, 3000)
    # project = "qt"
    project = "openstack"
    ans = pd.read_csv(f"addDelChecker_{project}.csv")
    ans_rq2 = list(ans[ans['Del_include?']==1]['NUMBER'])
    ans_rq3 = list(ans[ans['Add_include?']==1]['NUMBER'])

    rq2 = list(pd.read_csv("../../exe/_2_calculate/rq2.csv")["id"])
    print("RQ2: check  if old one has new one")
    check(rq2, ans_rq2, check_ranges)
    print("RQ2: check  if new one has old one")
    check(ans_rq2, rq2, check_ranges)
    rq3 = list(pd.read_csv("../../exe/_2_calculate/rq3.csv")["id"])
    print("RQ3: check  if old one has new one")
    check(rq3, ans_rq3, check_ranges)
    print("RQ3: check  if new one has old one")
    check(ans_rq3, rq3, check_ranges)