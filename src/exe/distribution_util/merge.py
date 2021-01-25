import ast
import csv
import glob
import json
import pickle

import pandas




#################################

def find_files(dname, filename):
    li = list()
    for name in glob.glob(dname + filename, recursive=True):
        li.append(name)

    return li

def concat_errors(err_paths):
    errors = {}
    for p in err_paths:
        with open(p, 'r') as f:
            lines = f.read().split("\n")
            for line in lines:
                tmp = line.split(",", 1)
                if len(tmp)==1:
                    break
                key = tmp[0].replace("\"", "")
                v = tmp[1].replace("\"", "").replace("[", "").replace("]", "").replace(" ", "")
                if v=="":
                    continue
                if key in errors:
                    errors[key].update(set(v.split(",")))
                else:
                    errors[key] = set(v.split(","))
    return errors


def concat_df(df_paths):
    li = list()
    for p in df_paths:
        with open(p, 'rb') as f:
            li.append(pickle.load(f))
    return pandas.concat(li, axis=0)





def print_error(project, errors, suffix):
    with open(f"{project}/{project}_errors{suffix}.txt", 'w') as f:
        for e in errors:
            f.write(f"{e}: {str(errors[e])}\n")
    with open(f"{project}/{project}_error_stats{suffix}.txt", 'w') as f:
        for e in errors:
            f.write(f"{e}: {len(errors[e])}\n")
    with open(f"{project}/{project}_errors{suffix}.json", 'w') as f:
        json.dump(errors, f)
    pass

def run(results_dir, project):
    dirname = f"{results_dir}/{project}/**-**/"
    rerun_dirname = f"{results_dir}/{project}/rerun/**/"
    all_dirname = f"{results_dir}/{project}/**/"

    df = concat_df(find_files(dirname, "df.pkl"))
    df_rerun = concat_df(find_files(rerun_dirname, "df.pkl"))
    pandas.concat([df, df_rerun], axis=0).to_pickle(f"{project}/{project}_df.pkl")

    errors = concat_errors(find_files(all_dirname, "error.csv"))

    r_err = errors['Please Rerun']
    for _, vals in df_rerun.iterrows():
        print("  ", vals['id'])
        id = str(int(vals['id']))
        if id in r_err:
            r_err.remove(id)# str や intのせいでエラー
    for key in errors:
        if key == 'Please Rerun':
            continue
        for v in errors[key]:
            id = str(int(v))
            if id in r_err:
                r_err.remove(str(int(v)))  # str や intのせいでエラー

    errors['Please Rerun'] = r_err
    for key in errors:
        errors[key] = list(errors[key])
    print_error(project, errors, suffix = "")


if __name__ == '__main__':
    results_dir = "/Volumes/home/kashiwa/satd/results"
    run(results_dir, "openstack")
    run(results_dir, "qt")


