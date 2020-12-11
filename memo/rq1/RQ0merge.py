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

#python2
#取れたdiff結果をマージする．
#error_idsをマージすることが先．
#temp_RQ0.json, temp_RQ0copy.json, temp_RQ0reverse.jsonの３種類が存在する．

#使い方：一括なら「python review_extract.py openstack nova」 という具合．
#部分的に実行するなら後ろに30001 45000とレビュー番号の範囲をつける．
#何もなければ1 999999と同義．

#手順
#1.全てのdiff_finallyから始まるファイルについて，a_commentとb_commentの長さを加算する
#2.どっちも足して1以上なら，SATDを含むコードレビューとしてリストに登録する．
#3.可能ならSATDを含む，含まない，SHAがなくて調査できない，の３つに分けておきたい．
#  lenがどちらかでも０以上ならSATD．そうでないなら両方のerror_idsの中にあればerror_idsとして結果から除外．
#  どちらかのerror_idsに含まれてなければnot SATDとして扱う．
#最終的な結果はSATD,not,不明の３種に分けることになると思う．list内の要素の重複の削除を行うことも忘れずに！
#優先順位：error>SATD>not? or SATD>error>not?


#curl https://(gerrit_name)/changes/(change_id)/revisions/(patch_id)/review/




#============================================================================
# SATDgetより引用
#============================================================================






#list2 = [list[0] for x in liar]

#return list #返り値はコメント，開始行，終了行の３要素を持ったリストのリスト





#er = {"error_ids":[]}
sub_name=''
#ここでconfigファイルを開いて言語情報を取る
with open('./config/'+ sub_name +'.txt','r') as h:
    string = h.readline()
temp_list = string.split(' ')
langs = temp_list[2:]
if "c" in langs:
    langs.append("h")
if "cpp" in langs:
    langs.extend(["hpp", "cc", "cxx", "cp", "hxx"])

error_ids = []
result = {"SATD_have":[], "not_have":[], "error_ids":[]}

error_signal = False #何度アクセスしてもエラーしか出ないやつの対策
#number...レビューナンバー
for number in json_dic[proj_name + "/" + sub_name]:
    list_count += 1

    skip_flag = False
    patch_skip = False
    lang_flag = False #言語が対象かどうかチェックするフラグ
    error_signal = False
    a_comments = 0
    b_comments = 0
    print "now number = " + str(number)
    print "now:" + str(list_count) +"/"+ str(len(json_dic[proj_name + "/" + sub_name]))
    patch = 1
    #if number in er["error_ids"]: #error_idsの中に存在すればそっちに番号をおく．
    #    result["error_ids"].append(number)
    #    continue
    path = dir_calc(proj_name, number) + 'query.json'
    
    with open(path, 'r') as h:
        #ここからjson->辞書形式で当該ファイルを読み込み
        dic = json.load(h)
    if isinstance(dic, dict): #たまにリストで囲まれてないことがあるので補正
        dic = [dic]
    if not ("current_revision" in dic[0]): #current情報のないものはerror分類
        error_ids.append(number)
        continue

    x = dic[0]["current_revision"] #出力は長さ１のリストの中に辞書が入ってるので[0]必要。
    total_patch = dic[0]["revisions"][x]["_number"] #その変更のパッチ総数．
    total_patch = int(total_patch) #パッチ総数
    while patch <= total_patch: #各パッチについてコメントとレビューの情報をみる．
        if skip_flag == True: #skipが出てたらもう調べようがないです
            patch += 1 #errorに分類すべきか？
            error_ids.append(number)
            break
        print "now_patch:" + str(patch) + "/" + str(total_patch)
        #script = 'curl "https://'+ address +'/changes/' + str(number) + '/revisions/' + str(patch) + '/files"'
        #input = api_get(script)
        path = dir_calc(proj_name, number) + 'diff_files_' + str(patch) + '.json' #そのパッチのdiffファイル情報を取る．
        if not os.path.isfile(path):
            error_ids.append(number)
            print "skipped"
            break
        with open(path, 'r') as h:
            #ここからjson->辞書形式で当該ファイルを読み込み
            try:
                file_dic = json.load(h)
            except ValueError: #たまにパッチが一部だけ存在しない場合がある．
                patch_skip = True
        if patch_skip == True:
            error_ids.append(number)
            patch_skip = False
            patch += 1
            break

            #ここで保存処理を入れる
            #各ファイルについてdiffを取る
        key_count = -1 #はじめは/COMMIT_MSGが来るのでその分１減らす
        for key in file_dic.keys(): #発見した各ファイルへの処理
            lang_flag = False
            key_count += 1
            if key == "/COMMIT_MSG":
                continue
            print key
            for la in langs:
                #print la
                if key.endswith(la): #サブプロジェクトに応じて変えるべき．forで．
                    lang_flag = True
                    lang = la
                    break

            if lang_flag == False: #言語が指定に一致しなかったら見ない
                continue

            print "now_file = " + key
            print "files:" + str(key_count) + "/" + str(len(file_dic) - 1)
            url_key = url_encode(key)
            path2 = dir_calc(proj_name, number) + 'diff_' + str(patch) + '_' + url_key + '.json'
            #print file
            if not os.path.isfile(path2):
                error_ids.append(number)
                print "skipped"
                patch += 1
                break
            with open(path2, 'r') as h:
                #ここからjson->辞書形式で当該ファイルを読み込み
                try:
                    dic = json.load(h)
                except ValueError: #パッチが消えててnot foundになってる場合
                    error_ids.append(number) #errorに分類する
                    patch += 1
                    break
            if not "a_comments" in dic:
                continue
            a_comments += len(dic["a_comments"])
            b_comments += len(dic["b_comments"])
        patch += 1
            #if a_comments >= 1 or b_comments >= 1: #消す？
            #    break #残りファイルの存在を確認しないとerrorをhaveと認識する場合がある
    
    #while patch部分終了
    if number in error_ids: #ここでnumberがerrorに分類されているかを見る
        continue
    total_comments = a_comments + b_comments
    if total_comments >= 1:
        result["SATD_have"].append(number)
    else:
        result["not_have"].append(number)

