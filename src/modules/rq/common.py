import pandas as pd


def is_deleted_added(changed_files):
    added = False#add
    deleted = False#delete
    for file in changed_files:# TODO: 違うファイルにまたがっていた場合
        a_satd_comments = _get_satd_comments(file['a_comments'])
        b_satd_comments = _get_satd_comments(file['b_comments'])
        print(a_satd_comments)
        #左にあって，右になかったらDelete
        #右にあって，左になかったらAdd
        if len(a_satd_comments)>0:
            deleted = True
        if len(b_satd_comments)>0:
            added = True
    return added, deleted

def _get_satd_comments(comments):
    out = []
    for comment in comments:
        if comment['include_SATD']:
            out.append(comment)
    return out


def get_unique(a_satd_comments, satd_array, revision):
    for comment in a_satd_comments:
        c = comment['comment']
        if not (c in satd_array.keys()): # when the satd appears for the first time
            info = {'revision': int(revision['revision']),
                    'filename': revision['filename'],
                    'start_line': int(comment['start_line']),
                    'end_line': int(comment['end_line']),
                    'url': int(revision['url'])
                    }
            satd_array[c] = info
    return satd_array


# FIXME: If there are satd comments that have the same contents in a file
def find_satd(d):
    exist_target_file = False
    a_satd = {}
    b_satd = {}
    for revision in d.results:
        if len(revision['changed_files']) > 0:
            exist_target_file = True
            for file in revision['changed_files']:# TODO: when the satd was moved in another file
                a_satd_comments = _get_satd_comments(file['a_comments'])
                b_satd_comments = _get_satd_comments(file['b_comments'])
                a_satd = get_unique(a_satd_comments, a_satd, revision)
                b_satd = get_unique(b_satd_comments, b_satd, revision)
    return exist_target_file, a_satd, b_satd


def find(d):
    added_satd = None
    deleted_satd = None
    for revision in d.results:
        if len(revision['changed_files']) > 0:
            a, d = is_deleted_added(revision['changed_files'])
            # TODO: 最初からある状態か？
            if a and (added_satd is None):
                added_satd = int(revision['revision'])
            if d and (deleted_satd is None):
                deleted_satd = int(revision['revision'])
    return added_satd, deleted_satd


def mark_satd(df: pd.DataFrame):
    arr_exist_target_file = []
    arr_add_satd = []
    arr_delete_satd = []
    arr_add_and_delete_satd = []
    arr_is_added_satd = []
    arr_is_deleted_satd = []
    for _, d in df.iterrows():
        exist_target_file, a_satd, b_satd = find_satd(d)
        arr_exist_target_file.append(exist_target_file)
        arr_add_satd.append(b_satd)
        arr_is_added_satd.append(len(b_satd) > 0)
        arr_delete_satd.append(a_satd)
        arr_is_deleted_satd.append(len(a_satd) > 0)
        ab_satd = {}
        for a in a_satd.keys():
            if a in b_satd.keys():
                if not b_satd[a]['revision'] == a_satd[a]['revision']:
                    ab_satd[a] = str(b_satd[a]) + '-' + str(a_satd[a])
                else:# TODO: when the satd is modified
                    pass
        arr_add_and_delete_satd.append(ab_satd)
    df['exist_target_file'] = arr_exist_target_file
    df['added_satd'] = arr_add_satd
    df['is_added_satd'] = arr_is_added_satd
    df['deleted_satd'] = arr_delete_satd
    df['is_deleted_satd'] = arr_is_deleted_satd
    df['added_and_deleted_satd'] = arr_add_and_delete_satd
    return df


def count_satd(df, clmn):
    wth = df[clmn]
    wth_out = df[clmn==False]
    return len(wth), len(wth_out)



def filter_out_self_review():  # list = そのリビジョンのコメント，list2 = その前までのリビジョンのコメント
    #TODO セルフレビュー除去．どこにある？
    return None
