import ast
import csv
import glob
import pickle

import pandas




#################################

def find_files(filename):
    li = list()
    for name in glob.glob(dirname + filename, recursive=True):
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
                print(key, v)
                if v=="":
                    continue
                if key in errors:
                    errors[key].extend(v.split(","))
                else:
                    errors[key] = v.split(",")
    return errors


def concat_df(df_paths):
    li = list()
    for p in df_paths:
        with open(p, 'rb') as f:
            li.append(pickle.load(f))
    df = pandas.concat(li, axis=0)
    return df

results_dir = "/Volumes/home/kashiwa/satd/results"
project = "qt"
if __name__ == '__main__':
    dirname = f"{results_dir}/{project}/**/"
    df = concat_df(find_files("df.pkl"))
    errors = concat_errors(find_files("error.csv"))
    df.to_pickle(f"{project}_df.pkl")
    with open(f"{project}_errors.txt", 'w') as f:
        f.write(str(errors))
