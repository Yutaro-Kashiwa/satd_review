import json

import pandas as pd

def check(checker, checkee, err, check_ranges=range(0, 1000000)):
    for r in checker:
        r = int(r)
        if not (check_ranges is None) and (r not in check_ranges):
            continue
        if r in checkee:
            # print("SAME:"+str(r))
            pass
        else:
            flg = True
            for key in err:
                if str(r) in err[key]:
                    print(f"{r}:{key}")
                    flg = False
                    break
            if flg:
                print(f"{r}:Program difference!!")

            # raise

if __name__ == '__main__':
    check_ranges = None
    project = "openstack"
    project = "qt"
    ans = pd.read_csv(f"addDelChecker_{project}.csv")
    ans_rq2 = list(ans[ans['Del_include?']==1]['NUMBER'])
    ans_rq3 = list(ans[ans['Add_include?']==1]['NUMBER'])
    errs = json.load(open(f"../../exe/distribution_util/{project}_errors.json", 'r'))
    rq2 = list(pd.read_csv(f"../../exe/_2_calculate/{project}/{project}_rq2.csv")["id"])
    print("RQ2: check  if the new program detect but the old program do not")
    # check(rq2, ans_rq2, errs, check_ranges)
    print("RQ2: check  if the old program detect but the new program do not")
    check(ans_rq2, rq2, errs, check_ranges)
    rq3 = list(pd.read_csv(f"../../exe/_2_calculate/{project}/{project}_rq3.csv")["id"])
    print("RQ3: check  if the new program detect but the old program do not")
    # check(rq3, ans_rq3, errs, check_ranges)
    print("RQ3: check  if the old program detect but the new program do not")
    check(ans_rq3, rq3, errs, check_ranges)

