def url_encode(string): #urlエンコード．スラッシュを%2Fに変えます．
    string = string.replace("/", "%2F")
    string = string.replace("#", "%23")
    string = string.replace(" ", "%20")
    return string

def url_decode(string): #urlデコード．%2Fをスラッシュに変えます．
    string = string.replace("%2F", "/")
    string = string.replace("%23", "#")
    string = string.replace("%20", " ")
    return string