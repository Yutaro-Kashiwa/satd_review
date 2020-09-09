import redis

from modules.review.GerritController import GerritController
from modules.review.GerritDao import GerritDao

if __name__ == "__main__":
    # TODO: データを取得して，daoに入れる
    # Redis に接続します
    project = 'qt'
    gc = GerritController(project)

    #
    # dao = GerritDao(project)
    #
    # l = dao.list()
    # for i in l:
    #     s = dao.get(i.decode())

