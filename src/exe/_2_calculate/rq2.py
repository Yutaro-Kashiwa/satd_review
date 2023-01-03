import pandas

from exe._2_calculate.rq1 import is_in_revised
from modules.utils import calc_rate
import seaborn as sns

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
sns.set(style="darkgrid")




def write(df, filename):
    arr = []
    initial = 0
    revised = 0
    for _, d in df.iterrows():
        for i in d["added_satd"]:
            rev = d["added_satd"][i]
            arr.append(rev)
            if rev == 1:
                initial += 1
            elif rev > 1:
                revised += 1
            else:
                raise
    all = initial + revised
    header = ['', 'initial', 'revised']
    num = ['num', initial, revised]
    rate = ['rate', calc_rate(initial, all), calc_rate(revised, all)]
    out_df = pandas.DataFrame([num, rate], columns=header)
    out_df.to_csv(filename)


    sns.histplot(data=arr, binwidth=1)
    plt.ylim([0,15000])
    plt.xlim([1,30])
    plt.savefig(f'{filename}.png')
    plt.close()

# NEED TO FIX
def make_list(df, data_col, out_filename):
    csv_contents = []
    for _, vals in df.iterrows():
        csv_line = []
        id = vals['id']
        print(vals)
        for comment, d in vals[data_col]:
            url = d['url']
            revision = d['revision']
            filename = d['filename']
            start_line = d['start_line']
            csv_line.append(id)
            csv_line.append(filename)
            csv_line.append(revision)
            csv_line.append(start_line)
            csv_line.append(f"{url}/{revision}/{filename}@{start_line}")
            csv_line.append(url)
            csv_line.append(comment)

            csv_contents.append(csv_line)
    out_df = pandas.DataFrame(csv_contents)
    out_df.to_csv(out_filename)
    pass


def run(project, df):
    print("**ADD timing (RQ2)**********************")
    df = df[(df['is_added_satd'] == True)].sort_values(by=["id"], ascending=True)
    df['is_in_revised'] = df.apply(lambda x: is_in_revised(x, 'added_satd'), axis=1)

    df[df.is_in_revised].drop('results', axis=1)\
        .drop('commit_message', axis=1)\
        .to_csv(f"{project}/{project}_rq2_row.csv")

    # make_list(df,'added_satd', f"{project}/{project}_rq2_manual_inspection.csv")

    write(df, f"{project}/{project}_statistics_add_timing.csv")
