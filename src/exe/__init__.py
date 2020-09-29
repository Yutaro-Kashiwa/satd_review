import configparser
import os
from pathlib import Path

print("************Loading conf files************")
CONFIG = configparser.ConfigParser()

HOMEDIR = Path(os.path.dirname(os.path.abspath(__file__))).parent.parent
CONFIG_DIR = HOMEDIR / 'conf'
# ---------------------
CONFIG.read(CONFIG_DIR / 'setting.ini')
ENV = dict()
ENV.update(CONFIG.items('ENV'))
ENV.update({'home_dir': HOMEDIR, 'input_dir': HOMEDIR/'input'})
print(ENV)
# ---------------------
RUN = dict()
RUN.update(CONFIG.items('RUN'))
# ---------------------
print(RUN)
print(CONFIG_DIR / 'projects' / (RUN['target_project'] + '.ini'))
CONFIG.read(CONFIG_DIR / 'projects' / (RUN['target_project'] + '.ini'))
PROJECT = dict()
PROJECT.update(CONFIG.items('PROJECT'))
PROJECT["sub_projects"] = PROJECT["sub_projects"].split(",")
print(PROJECT["sub_projects"])
PROJECT["bots"] = PROJECT["bots"].split(",")
print(PROJECT["bots"])
# ---------------------
print("HOMEDIR:", HOMEDIR)
print("CONFIG_DIR:", CONFIG_DIR)
print("PROJECT:", RUN['target_project'])
print(PROJECT)
print("************************************")
