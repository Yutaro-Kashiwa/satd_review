


if __name__ == "__main__":
    qt = {"name": "qt", "start": 0, "stop": 263350}
    os = {"name": "openstack", "start": 0, "stop": 673199}
    qt_tmp = {"name": "qt", "start": 72800, "stop": 72900}
    project = os
    unit = 1000
    workers = 10
    f = open("template.yaml")
    template = f.read()
    f.close()

    f = open(f"created/sample_{project['name']}.yaml", "w")
    cnt = 1
    for i in range(project['start'], project['stop'], unit):
        tmp = template
        tmp = tmp.replace("[PROJECT]", project['name'])
        tmp = tmp.replace("[NO]", str(cnt))
        tmp = tmp.replace("[START]", str(i))
        tmp = tmp.replace("[STOP]", str(i+unit))
        tmp = tmp.replace("[WORKER]", str(workers))

        f.write(tmp)
        f.write("\n")
        cnt += 1
    f.close()