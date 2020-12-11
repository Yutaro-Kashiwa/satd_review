def calc_rate(a, b, default_val = "-"):
    try:
        return a/b
    except ZeroDivisionError:
        return default_val



