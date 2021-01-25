
def run(project):
    unit = 1000
    workers = 5
    memory = "4Gi"
    cpu = "2"
    f = open("run_template.yaml")
    template = f.read()
    f.close()

    f = open(f"created/run_{project['name']}.yaml", "w")
    cnt = 1
    for i in range(project['start'], project['stop'], unit):
        tmp = template
        tmp = tmp.replace("[FILE]", "run.sh")
        tmp = tmp.replace("[PROJECT]", project['name'])
        tmp = tmp.replace("[NO]", str(cnt))
        tmp = tmp.replace("[START]", str(i))
        tmp = tmp.replace("[STOP]", str(i+unit))
        tmp = tmp.replace("[WORKER]", str(workers))
        tmp = tmp.replace("[MEMORY]", str(memory))
        tmp = tmp.replace("[CPU]", str(cpu))

        f.write(tmp)
        f.write("\n")
        cnt += 1
    f.close()

if __name__ == "__main__":
    qt = {"name": "qt", "start": 0, "stop": 263350}
    # qt = {"name": "qt", "start": 138200, "stop": 140000}
    os = {"name": "openstack", "start": 0, "stop": 673199}
    run(qt)
    run(os)