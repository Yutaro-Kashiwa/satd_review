import json
import sys
from ast import literal_eval

import pandas
from numpy import sort

from exe import load_project, HOMEDIR, ENV
from exe._1_detect import run
from exe._1_detect.run import write

not_allowed_list = ["program error", "know unknown problem", "anonymous file not found","SATD detector is too busy"]
def check_error(error):
    for n in not_allowed_list:
        if len(error[n]) > 0:
            raise RuntimeError

def rerun(d):
    for i in sort(d):
        i = int(i)
        df, error = run.run(project, i-1, i)
        check_error(error)

#"not target sub-project", "query file not found", "detail file not found", "diff file not found", "diff line file not found","no contents"
project_name = "openstack"
project_name = "qt"
targets = ['Please Rerun']

if __name__ == '__main__':
    args = sys.argv
    specific_no = None
    if len(args) > 2:
        project = load_project(args[1])
        specific_no = int(args[2])
        df, error = run.run(project, specific_no - 1, specific_no, workers=1)
        file_dir = f"{ENV['out_dir']}/{project['name']}/rerun/{specific_no}"
        write(df, error, file_dir)
    else:# read file
        project = load_project(project_name)
        error_file = f"{HOMEDIR}/src/exe/rerun/{project_name}_errors.json"
        with open(error_file, "r") as json_file:
            json_data = json.load(json_file)
        for t in targets:
            rerun(json_data[t])





