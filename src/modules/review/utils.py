def remove_bots_message(messages, bots):
    human_messages = []
    for m in messages:
        if not ("author" in m):
            # sometimes the data does not have author info, that's made by Gerrit Code Review
            continue
        if "username" in m["author"] and m["author"]["username"] in bots:
            continue
        else:
            human_messages.append(m)
    return human_messages


import re


def extract_inline_comments_number(messages):
    total_num = 0
    for m in messages:
        flg, num = detect_inline_comments(m["message"])
        if flg:
            total_num += num
        else:
            pass
    return total_num


def detect_inline_comments(text):
    match = re.search(r'^Patch Set \d+:.*\((\d+) inline comment.+', text, re.S)
    if match:
        assert len(match.groups()) == 1
        count = match.group(1)
        return True, int(count)
    else:
        return True, 0
