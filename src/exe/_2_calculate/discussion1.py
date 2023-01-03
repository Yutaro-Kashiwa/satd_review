from statistics import median

from exe._2_calculate.rq1 import accept_rate_ss


def is_in_initial(x, col):
    dic = x[col]
    for revision in dic.values():
        if revision == 1:
            return True
    return False


def run(project, df, exclude_one_time_accepted):
    df_with = df[df.is_added_satd == True].copy()
    if exclude_one_time_accepted:
        df_with = df_with[df_with.revisions > 1]
    df_with['is_satd_in_initial'] = df_with.apply(lambda x: is_in_initial(x, 'added_satd'), axis=1)
    df_satd_in_initial = df_with[df_with.is_satd_in_initial == True]
    df_satd_in_revised = df_with[df_with.is_satd_in_initial == False]
    print("initial_revisions", median(df_satd_in_initial.revisions))
    print("revised_revisions",median(df_satd_in_revised.revisions))
    df_initial_accepted = df_satd_in_initial[df_satd_in_initial.is_accepted]
    df_revised_accepted = df_satd_in_revised[df_satd_in_revised.is_accepted]
    print("accepted initial_revisions", median(df_initial_accepted.revisions))
    print("accepted revised_revisions", median(df_revised_accepted.revisions))
    print("--Acceptance Rate-----------------")
    # a: accepted reviews with SATD introduced in the initial changes
    # b: not accepted reviews with SATD introduced in the initial changes
    # c: accepted reviews with SATD introduced in the revised changes
    # d: not accepted reviews with SATD introduced in the revised changes
    a, b, c, d = len(df_initial_accepted), len(df_satd_in_initial) - len(df_initial_accepted), \
                 len(df_revised_accepted), len(df_satd_in_revised) - len(df_revised_accepted)
    print("initial", a+b, a, b,  a / (a + b))  # accepted rate in SATD introduced in initial changes
    print("revised",c+d, c, d,  c / (c + d))  # accepted rate in SATD introduced in revised changes

    accept_rate_ss(project, a, b, c, d, other="initial_vs_revised")

    df_without = df[df.is_added_satd == False].copy()
    df_without_accepted = df_without[df_without.is_accepted]
    a1, b1, c1, d1 = len(df_without_accepted), len(df_without) - len(df_without_accepted), \
                 len(df_revised_accepted), len(df_satd_in_revised) - len(df_revised_accepted)
    accept_rate_ss(project, a1, b1, c1, d1, other="non-satd_vs_revised")

    a2, b2, c2, d2 = len(df_without_accepted), len(df_without) - len(df_without_accepted), \
                 len(df_initial_accepted), len(df_satd_in_initial) - len(df_initial_accepted)
    accept_rate_ss(project, a2, b2, c2, d2, other="non-satd_vs_initial")