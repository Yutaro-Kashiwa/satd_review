import sys

import docker
import os

if __name__ == "__main__":
    client = docker.from_env()
    print(client.containers.list())
    print(client.images.list())
    # 応答確認
    if client.ping() == False:
        print("Ping Error", file=sys.stderr)
# -p 6379:6379 -v $1/$2:/data redis redis-server --appendonly yes
    data_dir = os.path.dirname(__file__)
    print(data_dir)
    client.containers.run(image="redis", name="redis", ports={'6379':6379}, auto_remove=1, volumes={data_dir: {'bind': '/data', 'mode': 'rw'}})#docker remove
