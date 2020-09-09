import math


def dir_calc(proj, id):
    id = int(id)
    ceil1 = int(math.ceil(id / 10000.0))  # math.ceil() ..切り上げ
    ceil2 = int(math.ceil(id / 200.0))
    a = (ceil1 - 1) * 10000 + 1
    b = (ceil1) * 10000
    c = (ceil2 - 1) * 200 + 1
    d = (ceil2) * 200
    string = './result/' + proj + '/' + str(a) + '-' + str(b) + '/' + str(c) + '-' + str(d) + '/' + str(id) + '/'
    return string


import os


