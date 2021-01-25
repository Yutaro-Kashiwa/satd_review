import json

from exe import HOMEDIR


def run(project):
    memory = "16Gi"
    cpu = "2"
    ###############
    error_file = f"{HOMEDIR}/src/exe/distribution_util/{project}/{project}_errors.json"
    with open(error_file, "r") as json_file:
        reruns = json.load(json_file)['Please Rerun']
        try:
            busy = json.load(json_file)['SATD detector is too busy']
            reruns.append(busy)
        except json.decoder.JSONDecodeError:
            pass


    ####
    f = open("run_template.yaml")
    template = f.read()
    f.close()

    f = open(f"created/rerun_{project}.yaml", "w")
    cnt = 1
    for i in reruns:
        i = int(i)
        tmp = template
        tmp = tmp.replace("[FILE]", "rerun.sh")
        tmp = tmp.replace("[PROJECT]", project)
        tmp = tmp.replace("[NO]", f"rerun-{cnt}")
        tmp = tmp.replace("[START]", str(i))
        tmp = tmp.replace("[STOP]", str(i)) # not used
        tmp = tmp.replace("[WORKER]", str(1)) # not used
        tmp = tmp.replace("[MEMORY]", str(memory))
        tmp = tmp.replace("[CPU]", str(cpu))

        f.write(tmp)
        f.write("\n")
        cnt += 1
    f.close()

if __name__ == "__main__":
    run("qt")
    # run("openstack")
