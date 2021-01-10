from ast import literal_eval

from exe import load_project, HOMEDIR
from exe._1_detect import main

project = "qt"
targets = ['program error', 'a']

if __name__ == '__main__':
    error_file = f"{HOMEDIR}/src/exe/rerun/{project}_errors.txt"
    project = load_project(project)
    with open(error_file, "r") as f:
        dct = literal_eval(f.read())
    for t in targets:
        if t in dct:
            for i in dct[t]:
                i = int(i)
                main.run(project, i-1, i)
                break
            break
        break
