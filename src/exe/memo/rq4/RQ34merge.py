# coding: UTF-8

import os
import commands
import sys
import re #正規表現用
import json
import codecs
import numpy
from time import sleep
import subprocess
import multiprocessing
import math
import urlparse
import csv

#python2
#使い方：「python review_extract.py openstack nova」 という具合．
#引数1=プロジェクト名/リポジリ名

#TODO list
#RQ3_url.json, RQ4_url.jsonを根こそぎ調べ，数を調べる．
#
#  csv形式で出力すべきか．

#さらにここで指定番号がセルフレビューであるか否かも出力しておきたい

#============================================================================
# SATDgetより引用
#============================================================================

def file_search(): #このままでは使えない
    #find ../DS/{project}って感じになりそう．
    #string = subprocess.call("pwd")
    #print string
    #コマンドが動作しない．何がおかしいんだろう？
    #script = r"find ./DS/stripe-java -name \"*.java\" -print" #エスケープなしでいける？
    #string = subprocess.call(script)
    #check_output = 返り値が標準出力になる．(他のコマンドだと０が返ってくるのでこれが必要）
    if rev_count == 1 or rev_count == list_length: #初めと最後は全部見つける必要あり．
        string = subprocess.check_output("find ./DS/" + proj_name + " -name *." + lang + " -print",  shell=True)
    else:
        string = subprocess.check_output("git diff --name-only " + before_hash + " " + h +  " --diff-filter=ACMR *." + lang,  shell=True, cwd= './DS/' + proj_name )
    #diff-filter..A=追加，C=コピー，M=変更，R=リネーム．のあったフォルダ．Dは削除．
    #でもD以外（小文字のdとするのが良さそう)
    #先に１つ前のリビジョン，後に今のリビジョンとすること．逆だと追加，除去の判定が逆転して死ぬ．
    #print string  #for test
    return string


def comment_get(url, hash):
    is_diff = False #i行目がdiff箇所に該当するか否かを入力する．
    list = []
    comments = ""
    temp_str = "" #一時保存用文字列
    multi_line = False
    after_solo = False #１行コメント(//系)の直後ならTrueにする．単行コメントが連続するなら文字列をつなぐ．
    javadoc = False #javadocの文法である疑いがあるならtrue.その場合@もあればyieldを行わない．
    now_line = 1
    start_line = 0
    intro_id = ""
    now_filename = url #チェックアウトに合わせて変えていくファイル名 .DS/proj_nameまでを消したもの
    #print "pass:" + url
    now_filename = now_filename.replace('./DS/' + proj_name + '/', '', 1)
    #print "now_filename:" + now_filename
    #ファイル開閉処理が入ってないやん．
    try:
        with open(url, "r+") as f:
            line = f.readline()
            while line: #ここhttps://除外をやっておく？
                if (re.search(re.escape(r"http://"), line) or re.search(re.escape(r"https://"), line)) and multi_line == False: #http exclude
                    if after_solo == True: #単行コメントの直後の場合の処理
                        yield {"proj_name":proj_name, "pass":url, "comment":comments, "start_line":start_line, "end_line":now_line - 1, "SHA":hash, "now_filename":now_filename, "last_SHA":hash}
                    after_solo = False
                    now_line += 1 #continue前に次の行への処理は必須
                    line = f.readline()
                    continue
                elif re.search(re.escape(r"/*"), line) and multi_line == True: # /*
                    if after_solo == True: #単行コメントの直後の場合の処理
                        yield {"proj_name":proj_name, "pass":url, "comment":comments, "start_line":start_line, "end_line":now_line - 1, "SHA":hash, "now_filename":now_filename, "last_SHA":hash}
                    after_solo = False
                    multi_line = True
                    comments = line[line.find("/*"):-1] + "\n"
                    if re.match(re.escape(r"/*"), comments):
                        javadoc = True
                    start_line = now_line
                elif re.search(re.escape(r"*/"), line) and multi_line == True : # */ bool=trueの条件も追加
                    comments += line[0:line.index("*/")]
                    multi_line = False
                    #list.append([comments, start_line, now_line])
                    #blameするならこのタイミングがいいか？
                    #intro_id = blame(url, start_line)
                    after_solo = False
                    if javadoc == False or re.search(re.escape(r"TODO"), comments) or re.search(re.escape(r"XXX"), comments) or re.search(re.escape(r"FIXME"), comments): #javadocでない，もしくはTODO,FIXME,XXXのいずれかの語を含むなら
                        yield {"proj_name":proj_name, "pass":url, "comment":comments, "start_line":start_line, "end_line":now_line, "SHA":hash, "now_filename":now_filename, "last_SHA":hash} #dictはキーの順番保持しない．
                    javadoc == False
                elif re.search(re.escape(r"//"), line) and multi_line == False : #//
                    temp_str = line[line.find("//"):-1] #改行文字は除外しない index -> find
                    #list.append([comments, now_line, now_line]) #要素追加
                    #intro_id = blame(url, now_line)
                    if after_solo == True:
                        comments += temp_str
                    else:
                        comments = temp_str
                        start_line = now_line
                        after_solo = True
                elif re.search(re.escape(r"/*"), line) and re.search(re.escape(r"*/"), line) and multi_line == False : # /* 〜〜〜 */
                    comments = line[line.find("/*"):line.index("*/")+1]
                    #list.append([comments, now_line, now_line]) #要素追加
                    #intro_id = blame(url, now_line)
                    yield {"proj_name":proj_name, "pass":url, "comment":comments, "start_line":now_line, "end_line":now_line, "SHA":hash, "now_filename":now_filename, "last_SHA":hash}
                elif multi_line :
                    comments += line
                    if not re.search(re.escape(r"*"), line):
                        javadoc = False #javadocは行ごとに*が入ってる．
                else:
                    if after_solo == True: #単行コメントの直後の場合の処理
                        yield {"proj_name":proj_name, "pass":url, "comment":comments, "start_line":start_line, "end_line":now_line - 1, "SHA":hash, "now_filename":now_filename, "last_SHA":hash}
                        after_solo = False
                    else:
                        after_solo = False
                now_line += 1
                line = f.readline()
    except IOError:
        print "IOError occured"
#list2 = [list[0] for x in liar]

#return list #返り値はコメント，開始行，終了行の３要素を持ったリストのリスト


#python系のコメント規則を持つもの(#,'''でコメントをつけられるもの)についてはこっちで対処する．
#def comment_get2(url, hash):
def comment_get2(script, diff_data):
    print "script_len+1 = " + str(len(script)) + ", diff_data_len = " + str(len(diff_data))
    after_diff = False
    is_diff = False #i行目がdiff箇所に該当するか否かを入力する．
    list = []
    comments = "" #複数行まとめた文字列
    temp_str = "" #一時保存用文字列
    result = []
    multi_line = False
    after_solo = False #１行コメント(//系)の直後ならTrueにする．単行コメントが連続するなら文字列をつなぐ．
    javadoc = False #javadocの文法である疑いがあるならtrue.その場合@もあればyieldを行わない．
    now_line = 1
    start_line = 0
    intro_id = ""
    #now_filename = url #チェックアウトに合わせて変えていくファイル名 .DS/proj_nameまでを消したもの
    #print "pass:" + url
    #now_filename = now_filename.replace('./DS/' + proj_name + '/', '', 1)
    #print "now_filename:" + now_filename
    #ファイル開閉処理が入ってないやん．
    try:
        for line in script:
            #line = f.readline() #入力がリスト形式なのでここ変更すべき
            #while line: #ここhttps://除外をやっておく？
                after_diff = is_diff
                is_diff = diff_data[now_line] #todo:out of rangeになる
                #http://関連の対策はpythonでは不要
                if re.search(re.escape(r"'''"), line) and multi_line == False: # /*
                    if after_solo == True and after_diff == True: #単行コメントの直後の場合の処理
                        result.append(comments)
                    after_solo = False
                    multi_line = True
                    comments = line[line.find("'''"):-1] + "\n"
                    if re.match(re.escape(r"'''"), comments):
                        javadoc = True
                    start_line = now_line
                elif re.search(re.escape(r"'''"), line) and multi_line == True : # */ bool=trueの条件も追加
                    comments += line[0:line.index("'''")]
                    multi_line = False
                    #list.append([comments, start_line, now_line])
                    #blameするならこのタイミングがいいか？
                    #intro_id = blame(url, start_line)
                    after_solo = False
                    #if javadoc == False or re.search(re.escape(r"TODO"), comments) or re.search(re.escape(r"XXX"), comments) or re.search(re.escape(r"FIXME"), comments):
                    if 1: #javadocの心配はないので
                        #javadocでない，もしくはTODO,FIXME,XXXのいずれかの語を含むなら
                        result.append(comments)
                    javadoc == False
                elif re.search(re.escape(r"#"), line) and multi_line == False and is_diff == True: #//
                    temp_str = line[line.find("#"):-1] #改行文字は除外しない index -> find
                    #list.append([comments, now_line, now_line]) #要素追加
                    #intro_id = blame(url, now_line)
                    if after_solo == True and is_diff == True:
                        comments += temp_str
                    else:
                        comments = temp_str
                        start_line = now_line
                        after_solo = True
                elif re.search(re.escape(r"'''"), line) and re.search(re.escape(r"'''"), line) and multi_line == False : # /* 〜〜〜 */
                    comments = line[line.find("'''"):line.index("'''")+1]
                    #list.append([comments, now_line, now_line]) #要素追加
                    #intro_id = blame(url, now_line)
                    result.append(comments)
                elif multi_line and is_diff == True:
                    comments += line
                    if not re.search(re.escape(r"*"), line):
                        javadoc = False #javadocは行ごとに*が入ってる．
                else:
                    if after_solo == True: #単行コメントの直後の場合の処理
                        result.append(comments)
                        after_solo = False
                    else:
                        after_solo = False
                now_line += 1
                #line = f.readline()
    except IOError:
        print "IOError occured"
    return result
#list2 = [list[0] for x in liar]

#return list #返り値はコメント，開始行，終了行の３要素を持ったリストのリスト



def detect(commentList):
    SATDComments = 0
    result = []
    temp_list = [] #value個ずつ読むときに使う．
    string = "" #detectorへの入力文字列
    id = 0
    id2 = 0
    value = 300 #１度に同時にでDetectorに処理してもらうコメント数．適宜増減させよう．
    p = os.getcwd() #SATDgetのディレクトリが出てきます
    print p
    det = p + "/srca/satd_detector.jar" #detectorのフルパス
    
    print commentList
    comlistlen = len(commentList) # commentListの長さ
    print "Detecting SATD..."
    for comment in commentList:
        
        #ここへ＊の消去処理を加えるべきか？
        n_delete = comment #\n_delete.つまり改行消した版の文字列をここへ突っ込む．
        n_delete = n_delete.replace('\r\n', ' ') #\rのreplaceも入れるべきか？
        n_delete = n_delete.replace('\n', ' ') #\rのreplaceも入れるべきか？
        n_delete = n_delete.replace('\\n', ' ')
        commentList[id] = n_delete
        
        #ここから大改造．
        temp_list.append(comment)
        #string += n_delete + "\n"
        string += n_delete.encode("utf-8") + "\n" #エラー対策
        
        if (id + 1) % value == 0 or comlistlen - id == 1: #100回読んだor commentListが最後なら実行
            satd_detector = subprocess.Popen("java -jar " + det + " test", stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True) # 最後の「,encoding='utf-8'」」はエラーが出たので省略．
            
            #string = string.encode("utf-8") #190620:一時停止中
            (stdout, stderr) = satd_detector.communicate(string) #ここが入力箇所．処理が遅い（約３秒）
            #print n_delete
            #Open a process with the SATD Detector tool to test the current comment text
            #print "STDOUT:" + stdout #必要に応じて使用する．
            strlist = [] #detectorの出力を行単位で入れる変数
            strlist = stdout.splitlines()
            list_len = len(temp_list) #要素が１００ない場合に使う．
            print "strlist:" + str(len(temp_list)) + " out_line:" + str(len(strlist)) + " id:" + str(id)
            #print "comment::" + n_delete
            #comment.commentTextをcomment["comment"]にすればいけるか？
            #そしてSATDならもう１つのリスト変数に移す動作を行う，と言った感じになるか．
            #print "..."
            for i in range(0,value): #0~99.ただし１００個入ってない場合の処理も必要．
                if i != 299 and i >= list_len:
                    print "list end at:" + str(i)
                    break
                #if stdout == '>SATD\n>': #
                elif "Not SATD" in strlist[i]:
                    pass
                elif "SATD" in strlist[i]:
                    result.append(temp_list[i])
                    SATDComments = SATDComments + 1
                else:
                    print "WHY????"
                id2 += 1
            temp_list = [] #１００個ごとに持ってきてた情報の消去．
            string = ""
            print "SATD found = " + str(SATDComments)
        else: #value回の節目以外はパス．
            pass
        id += 1 # commentごとのforループここまで
    
    return result

#異なるリビジョンの同一コメントを消す．
#やり方：resultリストに１つずつ要素を突っ込む．
#その際，resultリストの各要素見て，comment一致，ファイル名一致，SHA不一致の３条件を満たしていたら中断し，appendしない．
#通常版と比べ，SHAを条件から取り除いている．加えて，同じものが見つかった時，last_SHAを更新している．
def samecheck(list, list2): #list = そのリビジョンのコメント，list2 = その前までのリビジョンのコメント
    result = list2
    judge = True #同一のSATDを発見したらFalseにする．
    length = len(list) #いらないかも
    print "found comments = " + str(len(list))
    for x in range(len(list)): #そのリビジョンのコメントそれぞれについて
        #print x
        for y in range(len(result)): #その前までのリビジョンのコメントと比較する．
            #でかいデータならlen(list2)ではなくlen(result)にすべし．
            if list[x]["comment"] == result[y]["comment"] and list[x]["now_filename"] == result[y]["now_filename"]:
                #print "found same SATD"
                judge = False
                result[y]["last_SHA"] = list[x]["SHA"] #ここ追加しました
                break
        if judge == True:
            result.append(list[x])
        else:
            judge = True
    print "unique comments = " + str(len(result))
    return result


#============================================================================
# original
#============================================================================




def dir_calc(proj, id): #パッチIDに応じて保存先を計算する．最後はスラッシュ付き．
    id = int(id)
    ceil1 = int(math.ceil(id/10000.0)) #math.ceil() ..切り上げ
    ceil2 = int(math.ceil(id/200.0))
    a = (ceil1 - 1) * 10000 +1
    b = (ceil1) * 10000
    c = (ceil2 - 1) * 200 +1
    d = (ceil2) * 200
    #print id
    #print ceil1
    #print ceil2
    #print a
    #print b
    #print c
    #print d
    string = './result/' + proj_name + '/' + str(a) + '-' + str(b) + '/' + str(c) + '-' + str(d) + '/' + str(id) + '/'
    return string

def api_get(script): #引数を実行し，初めの)]}'を抜いた文字列を返します．
    input = subprocess.check_output(script, shell=True, cwd='./')
    #inputから")]}'"を除外する．
    input = input.replace(")]}'\n", "", 1)
    return input

def write_read(input, path): #指定パスに書き込みを行い，さらに読み込んで辞書を返り値に取る
    with open(path, 'w') as f:
        f.write(input)
    with open(path, 'r') as h:
        #ここからjson->辞書形式で当該ファイルを読み込み
        dic = json.load(h)
    return dic

def url_encode(string): #urlエンコード．スラッシュを%2Fに変えます．
    string = string.replace("/", "%2F")
    return string

def url_decode(string): #urlデコード．%2Fをスラッシュに変えます．
    string = string.replace("%2F", "/")
    return string


###########################################################################
#保存形式は？
#レビューのプロジェクト情報.. リストでプロジェクト名を保存させるのはメモリオーバーが考えられるから賢明でないと思う．
#
#openstackのgerritname .. review.opendev.org
#qt .. codereview.qt-project.org



#必要ディレクトリの準備
now_end = 673199 #qt=263350


proj_name = "openstack"
sub_name = "nova"
lang = "py"


if sys.argv >= 4: #プログラム名の後に引数があるなら(argvはプログラム名も数に含めている)
    argvs = sys.argv
    proj_name = argvs[1]
    sub_name = argvs[2]
    ignore = argvs[3] #引数に値が存在すれば，その分だけすでに終わってることにする
    ignore = int(ignore)
else:
    ignore = 0

#number = ignore #number..現在見ているレビューidのこと．


if proj_name == "openstack":
    address = "review.opendev.org" #address..プロジェクトによる固有ドメイン
    now_end = 673199
if proj_name == "qt":
    address = "codereview.qt-project.org"
    now_end = 263350


#number = int(number) #文字列ー＞数値

#SATD_haveの情報を呼び出す
with open('./dict/result_RQ0_' + sub_name + '.json', 'r') as g:
    json_dic = json.load(g)

#ignoreについての処理は未対応．

list_count = 0 #進捗表示用変数
#error_ids = [] #checkoutに失敗したIDを格納する．
path1 = './data/result_RQ34_'+ sub_name +'.csv' #レビュ中で追加/削除されたSATDの数
#(レビュー単位)
path2 = './data/result_RQ3_comments_'+ sub_name +'.csv' #削除されたコメントの内容
path3 = './data/result_RQ4_comments_'+ sub_name +'.csv' #追加されたコメントの内容
path4 = './data/result_del_unreview_'+ sub_name +'.csv' #追加されたコメントの内容
path5 = './data/result_add_unreview_'+ sub_name +'.csv' #追加されたコメントの内容

'''
if int(ignore) != 0: #途中から始める時の処理(未作成)
    with open(path1, 'r') as h:
        result = json.load(h)
    with open(path2, 'r') as h:
        result2 = json.load(h)
    with open(path3, 'r') as h:
        result3 = json.load(h)
    with open(path4, 'r') as h:
        result4 = json.load(h)
        '''
if 1:
    output1 = "NUMBER,COMMENTS,RQ3(deleted),RQ4(added),del_unreview,add_unreview,is_self\n"
    output2 = "NUMBER,FILE_NAME,PATCH,LINE,COMMENT\n" #2,4同じ
    output3 = "NUMBER,FILE_NAME,PATCH,lastFOUND,patchEND,LINE,lastFOUND,change_id,COMMENT\n"
    output4 = "NUMBER,FILE_NAME,PATCH,LINE,COMMENT\n"
    with open(path1, 'w') as f: #ヘッダ書き込み
        f.write(output1)
    with open(path2, 'w') as f:
        f.write(output2)
    with open(path3, 'w') as f:
        f.write(output3)
    with open(path4, 'w') as f:
        f.write(output4)
    with open(path5, 'w') as f:
        f.write(output3)

#with open(path, 'r') as h:
#    er = json.load(h)
#result["error_ids"] = er["error_ids"]

#TODO:変更ごとに「RQ34_」から始まるファイルを取り，
#「NoごとのRQ3,4の該当コメント数のcsv」「RQ3に該当するコメントcsv」「RQ4に該当するコメントcsv」
#を出力する．

#RQ34_数についてcsvの属性内容
#NUMBER=change_idのこと．
#RQ3=レビュー中に削除されたSATDの数
#RQ4=レビュー中に追加されたSATDの数

#RQ3_comments_nova.csv, RQ4_comments_nova.csvの属性内容
#NUMBER=change_id
#FILE_NAME=該当したファイル
#COMMENT=コメント内容



#number...レビューナンバー
for number in json_dic["SATD_have"]:
    list_count += 1
    RQ3_len = 0 #number単位でlenの合計を取る
    RQ4_len = 0
    del_unreview_len = 0
    add_unreview_len = 0
    change_id = ""
    if int(number) < int(ignore): #途中から始めたいとき用
        continue
    skip_flag = False
    patch_skip = False
    print ""
    print "now number = " + str(number)
    print "now:" + str(list_count) +"/"+ str(len(json_dic["SATD_have"]))
    #先ずは全パッチ情報をゲットせよ．
    #パッチ総数をどうやってとるか？
    patch = 1
    #ここでchange_idを取得する
    path = dir_calc(proj_name, number) + 'query.json'
    with open(path, 'r') as h:
        #ここからjson->辞書形式で当該ファイルを読み込み
        dic = json.load(h)
    change_id = dic[0]["change_id"]
    change_id = change_id.encode("utf-8")
    
    path = dir_calc(proj_name, number) + 'RQ34_*' #保存規則変わったけどこっちはこのままでOK
    try:
        string = subprocess.check_output("find " + path ,  shell=True)
    #findで街灯がない場合どう例外処理する？
    except subprocess.CalledProcessError:
        continue

    file_list = string.splitlines()
    #with open(path, 'w') as f:
    #    f.write(input)
    for file in file_list:
        with open(file, 'r') as h:
            #ここからjson->辞書形式で当該ファイルを読み込み
            dic = json.load(h)
        RQ3_comments = dic[0]["RQ3comments"]
        RQ4_comments = dic[0]["RQ4comments"]
        add_unreview = dic[0]["RQ5comments"]
        del_unreview = dic[0]["del_unless_review"]
        RQ3_len += len(RQ3_comments)
        RQ4_len += len(RQ4_comments)
        del_unreview_len += len(del_unreview)
        add_unreview_len += len(add_unreview)

        #UnicodeDecodeErrorが出るので一旦スルー
        
        #不具合：csv開くとセルが,で別れちゃう
        #出力形式も考え直す必要あり
        for com in RQ3_comments:
            comment = com["comment"]
            comment = comment.encode("utf-8") #UnicodeEncodeErrorが出るので
            line = com["start_line"]
            comment = re.sub('\"', '\"\"', comment) #セルを跨がないようにする処理
            #comment = '"' + comment + '"'
            f_name = com["pass"]
            f_name = f_name.encode("utf-8")
            patch = com["patch"]
            #resultディレクトリと.jsonを引く
            #minus_string = dir_calc(proj_name, number)+'RQ34_'
            #f_name = f_name.replace(minus_string, '', 1)
            #f_name = f_name.replace('.json', '', 1)
            output = str(number) + "," + f_name + "," + str(patch) + "," + str(line) + ',"' + comment + '"\n'
            with open(path2, 'a') as f:
                f.write(output)
        for com in RQ4_comments:
            comment = com["comment"]
            comment = comment.encode("utf-8")
            line = com["start_line"]
            comment = re.sub('\"', '\"\"', comment)
            #comment = '"' + comment + '"'
            f_name = com["pass"]
            f_name = f_name.encode("utf-8")
            patch = com["patch"]
            l_patch = com["last_patch"] #最後に見つけたパッチ
            t_patch = com["total_patch"]
            l_sl = com["last_startline"]
            #resultディレクトリと.jsonを引く
            #minus_string = dir_calc(proj_name, number)+'RQ34_'
            #f_name = f_name.replace(minus_string, '', 1)
            #f_name = f_name.replace('.json', '', 1)
            output = str(number) + "," + f_name + "," + str(patch) + "," + str(l_patch) + "," + str(t_patch) + "," + str(line) + "," + str(l_sl) + "," + change_id + ',"' + comment + '"\n'
            with open(path3, 'a') as f:
                f.write(output)
        for com in add_unreview: #本当はdel_unreviewを先にしたほうが順序的に綺麗
            comment = com["comment"]
            comment = comment.encode("utf-8")
            line = com["start_line"]
            comment = re.sub('\"', '\"\"', comment)
            #comment = '"' + comment + '"'
            f_name = com["pass"]
            f_name = f_name.encode("utf-8")
            patch = com["patch"]
            l_patch = com["last_patch"] #最後に見つけたパッチ
            t_patch = com["total_patch"]
            l_sl = com["last_startline"]
            #resultディレクトリと.jsonを引く
            #minus_string = dir_calc(proj_name, number)+'RQ34_'
            #f_name = f_name.replace(minus_string, '', 1)
            #f_name = f_name.replace('.json', '', 1)
            output = str(number) + "," + f_name + "," + str(patch) + "," + str(l_patch) + "," + str(t_patch) + "," + str(line) + "," + str(l_sl) + "," + change_id + ',"' + comment + '"\n'
            with open(path5, 'a') as f:
                f.write(output)
        for com in del_unreview:
            comment = com["comment"]
            comment = comment.encode("utf-8")
            line = com["start_line"]
            comment = re.sub('\"', '\"\"', comment)
            #comment = '"' + comment + '"'
            f_name = com["pass"]
            f_name = f_name.encode("utf-8")
            patch = com["patch"]
            #resultディレクトリと.jsonを引く
            #minus_string = dir_calc(proj_name, number)+'RQ34_'
            #f_name = f_name.replace(minus_string, '', 1)
            #f_name = f_name.replace('.json', '', 1)
            output = str(number) + "," + f_name + "," + str(patch) + "," + str(line) + ',"' + comment + '"\n'
            with open(path4, 'a') as f:
                f.write(output)
                

    #さらにここでセルフレビューか否かの情報も取得する
    s = './data/self_review_' + sub_name + '.json'
    with open(s, 'r') as g:
        dic = json.load(g)
    
    is_self = 0
    if number in dic["self_review"]:
        is_self = 1


    #全マージした番号データを使って番号に一致があればセルフとして扱う
    
    comment_total = RQ3_len + RQ4_len + del_unreview_len + add_unreview_len
    output = str(number) + "," + str(comment_total) + "," + str(RQ3_len) + "," + str(RQ4_len) + "," + str(del_unreview_len) + "," + str(add_unreview_len) + "," + str(is_self) + "," + "\n"
    with open(path1, 'a') as f:
        f.write(output)
#forここまで

#ここでさらにデータ統合用ファイルを作成
with open(path1, 'r') as f: #result_RQ34_(sub).csvを開く
    r = csv.reader(f)
    reader = [row for row in r] #２次元リスト化

com = 0
RQ3comments = 0
RQ4comments = 0
del_unreview = 0
add_unreview = 0
for row in reader[1:]: #[2]=status, #[3]=patch_num
    com += int(row[1])
    RQ3comments += int(row[2])
    RQ4comments += int(row[3])
    del_unreview += int(row[4])
    add_unreview += int(row[5])

#コメント数合計結果のcsvファイル作成
out_path = './data/RQ34_' + proj_name + '_' + sub_name + '.csv'
output = "PROJ,SUB_NAME,COMMENTS,RQ3(deleted),RQ4(added),del_unreview,add_unreview\n"
with open(out_path, 'w') as f:
    f.write(output)
    write_list = [proj_name, sub_name, com, RQ3comments, RQ4comments, del_unreview, add_unreview]
    write_list = map(str, write_list) #まとめて文字列にする
    out_str = ",".join(write_list)
    f.write(out_str)
    
print "finish!"

#もしかしたらunicode文字への変換処理が必要かもしれない．

#path = './dict/result_RQ34_' + sub_name + '.json'

#with open(path, 'w') as e:
#    json.dump(result, e)


#パッチの数の取り方．．currentで取ってjsonに変換した後に値を取得しカウントダウン式に取る？

#レビューコメントの取り方
#while patch <= total_patch: #各パッチについてコメントとレビューの情報を取る
#script = 'curl "https://'+ address +'/changes/' + str(number) + '/revisions/' + str(patch) + '/comments"'
