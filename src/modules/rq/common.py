import pandas as pd


def check_satd_action(changed_files):
    a = False#add
    d = False#delete
    for file in changed_files:# TODO: 違うファイルにまたがっていた場合
        a_satd_comments = _get_satd_comments(file['a_comments'])
        b_satd_comments = _get_satd_comments(file['b_comments'])
        if len(a_satd_comments)>0:
            a = True
        if len(b_satd_comments)>0:
            d = True
    return a, d

def _get_satd_comments(comments):
    out = []
    for comment in comments:
        if comment['include_SATD']:
            out.append(comment)
    return out


def mark_satd(df: pd.DataFrame):
    arr_exist_target_file = []
    arr_add_satd = []
    arr_delete_satd = []
    for _, d in df.iterrows():
        exist_target_file = False
        added_satd = None
        deleted_satd = None
        for revision in d.results:
            if len(revision['changed_files']) > 0:
                exist_target_file = True
                a, d = check_satd_action(revision['changed_files'])
                #TODO: 最初からある状態か？
                if a and (added_satd is None):
                    added_satd = int(revision['revision'])
                if d and (deleted_satd is None):
                    deleted_satd = int(revision['revision'])
        arr_exist_target_file.append(exist_target_file)
        arr_add_satd.append(added_satd)
        arr_delete_satd.append(deleted_satd)
    df['exist_target_file'] = arr_exist_target_file
    df['added_satd'] = arr_add_satd
    df['deleted_satd'] = arr_delete_satd
    return df


def count_satd(df, clmn):
    wth = df[clmn]
    wth_out = df[clmn==False]
    return len(wth), len(wth_out)

