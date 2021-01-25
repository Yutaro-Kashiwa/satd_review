import re

import pandas as pd
if __name__ == '__main__':

    line = "  /* \"top5\"*/ \u003c\u003c \"top5,child0\"  \u003c\u003c \"top5,child1\"    \u003c\u003c \"top5,child2\"  \u003c\u003c"
    a = re.sub('".+?"', '""', line)
    print(a)
