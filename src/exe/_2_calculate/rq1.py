import pandas
import scipy.stats
import math

from exe._2_calculate.all import read_pkl
from modules.utils import calc_rate


def accept_rate_ss(project, a, b, c, d):
    # 検定：比率の差の検定（＝カイ二乗検定）
    crosstab = pandas.DataFrame([[a, b], [c, d]])
    x2, p, dof, expected = scipy.stats.chi2_contingency(crosstab)
    print("p-value = " + str(p))

    accepted_header = ['--Acceptance Rate-----------------', '', '']
    accepted_p = ['p-value', '', p]
    # 効果量：SQRT(カイ二乗値/N) # NOTE: effect size should not be calculated for rates
    # phi = math.sqrt(x2 / (a+b+c+d))
    # print("Effect size = " + str(phi))
    # accepted_eff = ['effect_size', '', phi]
    out_df = pandas.DataFrame([accepted_header, accepted_p])#accepted_eff
    out_df.to_csv(f"{project}/{project}_acc_statistics.csv", mode='w', header=False)


def revision_ss(project, a, b):
    # 検定：U検定
    U, p = scipy.stats.mannwhitneyu(a, b)
    print("p-value = " + str(p))
    # 効果量：Z-score / SQRT(N)
    # mannshitneyuではZ-scoreを出してくれないので手動で計算するしかないらしい
    E = (len(a) * len(b)) / 2  # 期待値
    V = math.sqrt(len(a) * len(b) * (len(a) + len(b) + 1) / 12) # 分散
    Z = (U - E) / V  # Z値
    r = math.sqrt(Z ** 2 / (Z ** 2 + len(a) + len(b) - 1))  # r値
    print("Effect size = " + str(r))
    revision_header = ['--Revision-----------------', '', '']
    revision_p = ['p-value', '', p]
    revision_eff = ['effect_size', '', r]
    out_df = pandas.DataFrame([revision_header, revision_p, revision_eff])
    out_df.to_csv(f"{project}/{project}_rev_statistics.csv", mode='w', header=False)

#回帰係数とかなんとか．まだコピペしただけの状態.
def rq1checker(path, mode):  # modeはSATDがある方については1，ない方については2を記述する
    with open(path, 'r') as f:
        r = csv.reader(f)
        reader = [row for row in r]  # ２次元リスト化

    if mode == 1:
        merged_list = []  # ひとまずはSATDを持つもの限定でとる
        rejected_list = []
    merged_count = 0  # MERGEDになってるレビューの数
    patch_sum = 0  # パッチ数を全部たす
    p_array = []  # 中央値用の配列
    # reader.pop(0) #はじめの行を除外する

    for row in reader[1:]:  # [2]=status, #[3]=patch_num
        patch_sum += int(row[3])
        p_array.append(int(row[3]))
        if row[2] == "MERGED":
            merged_count += 1
            if mode == 1:
                merged_list.append(int(row[1]))
        elif mode == 1:
            rejected_list.append(int(row[1]))

    length = len(reader) - 1
    if length == 0:
        patch_ave = 0
        patch_med = 0
        not_rate = 0
    else:
        patch_ave = float(patch_sum) / float(length)
        patch_med = float(numpy.median(p_array))
        not_rate = float(length - merged_count) / float(length) * 100

    print
    " size  MERGED  notMERGED  not_rate  patch_sum  patch_ave  patch_med"
    print
    "%5d  %6d  %9d    %3.2f%%  %9d       %3.2f       %3.2f" % (
    length, merged_count, length - merged_count, not_rate, patch_sum, patch_ave, patch_med)

    if mode == 1:
        mode_str = "SATD_have"
    elif mode == 2:
        mode_str = "not_have"
    write_list = [proj_name, sub_name, mode_str, length, merged_count, length - merged_count, str(not_rate) + "%",
                  patch_sum, patch_ave, patch_med]
    write_list = map(str, write_list)  # まとめて文字列にする
    with open(out_path, 'a') as f:
        out_str = ",".join(write_list)
        f.write(out_str + "\n")

    if mode == 1:
        output_json = {"merged_list": merged_list, "rejected_list": rejected_list}
        out_path2 = './data/rejected_list_' + sub_name2 + '.json'
        with open(out_path2, 'w') as e:
            json.dump(output_json, e)


def rq1(project, df):
    print("**RQ1********************")
    df_with = df[(df.is_added_satd == True) | (df.is_deleted_satd == True)]
    df_without = df[((df.is_added_satd == True) | (df.is_deleted_satd == True)) == False]
    df_with_accepted = df_with[df_with.is_accepted]
    df_without_accepted = df_without[df_without.is_accepted]
    print("--Statistics-----------------")
    header = ['', "SATD", "non-SATD"]
    num = ['num', len(df_with), (len(df_without))]
    accepted_num = 'accepted_num', len(df_with_accepted), (len(df_without_accepted))
    accepted_rate = ['accepted_rate', calc_rate(len(df_with_accepted), len(df_with)),
                     calc_rate(len(df_without_accepted), len(df_without))]
    min_revisions = ['min_revisions', df_with['revisions'].min(), df_without['revisions'].min()]
    mean_revisions = ['mean_revisions', df_with['revisions'].mean(), df_without['revisions'].mean()]
    median_revisions = ['median_revisions', df_with['revisions'].median(), df_without['revisions'].median()]
    max_revisions = ['max_revisions', df_with['revisions'].max(), df_without['revisions'].max()]
    out_df = pandas.DataFrame([num, accepted_num, accepted_rate, min_revisions, mean_revisions, median_revisions, max_revisions], columns=header)
    out_df.to_csv(f"{project}/{project}_statistics.csv")

    print("--Acceptance Rate-----------------")
    a, b, c, d = len(df_with_accepted), len(df_with) - len(df_with_accepted), \
                 len(df_without_accepted), len(df_without) - len(df_without_accepted)
    accept_rate_ss(project, a, b, c, d)

    print("--Revision-----------------")
    revision_ss(project, df_with.revisions, df_without.revisions)




