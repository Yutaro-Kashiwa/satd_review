# coding: UTF-8

import os
import sys
import re #正規表現用
import json
import subprocess
import math


#保存形式は？
#レビューのプロジェクト情報.. リストでプロジェクト名を保存させるのはメモリオーバーが考えられるから賢明でないと思う．
#
#openstackのgerritname .. review.opendev.org
#qt .. codereview.qt-project.org



#number = int(number) #文字列ー＞数値

with open('./dict/' + proj_name + '.json', 'r') as g: #projで一旦やってみよ
    json_dic = json.load(g)


#number...レビューナンバー
for number in json_dic[proj_name + "/" + sub_name]:
    list_count += 1
    if int(number) < int(temp_start): #途中から始めたいとき用
        continue
    if int(number) > int(end): #番号が終点を超えたら終了
        break
    skip_flag = False
    patch_skip = False
    lang_flag = False #言語が対象かどうかチェックするフラグ
    error_signal = False
    print("\n")
    print("now number = " + str(number))
    print("now:" + str(list_count) +"/"+ str(len(json_dic[proj_name + "/" + sub_name])))
    #先ずは全パッチ情報をゲットせよ．
    #パッチ総数をどうやってとるか？
    patch = 1
    script = 'curl "https://'+ address +'/changes/?q=' + str(number) + '&o=CURRENT_REVISION"' #このコマンドでないとcurrent_revisionが出ない

    path = dir_calc(proj_name, number) + 'query.json'
    input = api_get(script)
    with open(path, 'w') as f:
        f.write(input)
    
    with open(path, 'r') as h:
        #ここからjson->辞書形式で当該ファイルを読み込み
        dic = json.load(h)
    #if isinstance(dic, dict): #たまにリストで囲まれてないことがあるので補正
    #    dic = [dic]
    if not ("current_revision" in dic[0]):
        error_ids.append(number)
        temp_dict = {"error_ids":error_ids}
        with open(t_path, 'w') as e:
            json.dump(temp_dict, e)
        print("skipped") #NEWかABANDONEDの場合はcurrentが存在しない．
        continue #今更だがここでさらにdetailを取って[messages]リストからそれぞれの要素について[_revision_number]を調べ最大値を取れば良いのでは・・？
    x = dic[0]["current_revision"] #出力は長さ１のリストの中に辞書が入ってるので[0]必要。
    total_patch = dic[0]["revisions"][x]["_number"] #その変更のパッチ総数．
    total_patch = int(total_patch) #パッチ総数
    while patch <= total_patch: #各パッチについてコメントとレビューの情報を取る
        if skip_flag == True: #skipが出てたらもう調べようがないです
            patch += 1
            break
        print("now_patch:" + str(patch) + "/" + str(total_patch))
        script = 'curl "https://'+ address +'/changes/' + str(number) + '/revisions/' + str(patch) + '/files"'
        input = api_get(script)
        path = dir_calc(proj_name, number) + 'diff_files_' + str(patch) + '.json'

        if not os.path.isfile(path): #該当ファイル名がないならAPIデータ書き込み
            #(できればオプションですでにデータがあるときに上書きするか何もしないかを設定したい)
            with open(path, 'w') as f:
                f.write(input)
        with open(path, 'r') as h:
            #ここからjson->辞書形式でファイル名一覧を読み込み
            try:
                file_dic = json.load(h)
            except ValueError: #たまにパッチが一部だけ存在しない場合がある．
                patch_skip = True
        if patch_skip == True:
            patch_skip = False
            patch += 1
            continue

            #ここで保存処理を入れる
            #各ファイルについてdiffを取る
        key_count = -1 #はじめは/COMMIT_MSGが必ず来るのでその分１減らす

        for key in file_dic.keys(): #発見した各ファイルへの処理
            lang_flag = False
            key_count += 1
            if key == "/COMMIT_MSG":
                continue
            print(key)
            for la in langs:
                #print la
                if key.endswith(la): #サブプロジェクトに応じて変えるべき．forで．
                    lang_flag = True
                    lang = la
                    break
            if lang_flag == False: #言語が指定に一致しなかったら見ない
                continue

            print("now_file = " + key)
            print("files:" + str(key_count) + "/" + str(len(file_dic) - 1))
            url_key = url_encode(key)
            script = 'curl "https://'+ address +'/changes/' + str(number) + '/revisions/' + str(patch) + '/files/' + url_key + '/diff"'
            input = api_get(script) #APIデータ取得
            if input.startswith("<!DOCTYPE HTML PUBLIC") == True: #api_getが異常終了した時に使う
                skip_flag = True
                print("skipped")
                error_ids.append(number)
                temp_dict = {"error_ids":error_ids}
                with open(t_path, 'w') as e:
                    json.dump(temp_dict, e)
                break
            #ここから差分行の情報を取る必要がある．
            path2 = dir_calc(proj_name, number) + str(patch) + '_' + url_key + '.json' #仮．本番までには必ずどこかへしっかり保存せよ
            dic = write_read(input, path2) #変数dicにdiffデータの辞書を読み込み
            #ここからは別関数に任せたほうがいいかも．
            a_script = []
            b_script = []
            #a_line = 1
            #b_line = 1
            a_diff = [False] #配列[i] = i行目にコメントが存在するか
            b_diff = [False] #0行目は必ずFalseで
            for diff in dic["content"]:
                for key2 in diff.keys(): #前のと後のやつの差分行の登録
                    #k = diff[key2]
                    if key2 == "a":
                        for array in diff[key2]:
                            #print " diff[a]= " + str(diff[key2])
                            #a_script += array
                            a_diff.append(True)
                            a_script.append(array)
                            #a_line += 1
                    if key2 == "b":
                        for array in diff[key2]:
                            #print " diff[b]= " + str(diff[key2])
                            #b_script += array
                            b_diff.append(True)
                            b_script.append(array)
                            #b_line += 1
                    if key2 == "ab":
                        for array in diff[key2]:
                            #print " diff[ab]= " + str(diff[key2])
                            #a_script += array
                            #b_script += array
                            a_script.append(array)
                            b_script.append(array)
                            a_diff.append(False)
                            b_diff.append(False)
                            #a_line += 1
                            #b_line += 1
                    if key2 == "skip":
                        skip_flag = True
                        print("skipped")
                        error_ids.append(number)
                        #t_path = './dict/temp_RQ0_'+ sub_name +'.json' ####コピー時注意 #t_path記述箇所移動済み
                        temp_dict = {"error_ids":error_ids}
                        with open(t_path, 'w') as e:
                            json.dump(temp_dict, e)
                if skip_flag == True: #skipが出てたらもう調べようがないです
                    break
                #a_line += 1
                #b_line += 1
                #とった情報をどう保存する？フルパス名で保存．
                #a,b_comments...ジェネレータをなんとかしないとだめ
                #print "a_script = " + str(a_script)
                #print "b_script = " + str(b_script)
            if skip_flag == True: #skipが出てたらもう調べようがないです
                break
            #error_idsに加える例外処理が必要
            if lang in langtype1: #言語に応じて異なるメソッドでdiffであるコメントを抽出
                a_comments = comment_get(a_script, a_diff, "/*", "*/", "//")
                b_comments = comment_get(b_script, b_diff, "/*", "*/", "//")
            elif lang in langtype2:
                a_comments = comment_get2(a_script, a_diff)
                b_comments = comment_get2(b_script, b_diff)
            elif lang in langtype3: #visualbasic系には複数行コメントはないのでテキトーな無理文字列でごまかす
                a_comments = comment_get(a_script, a_diff, "fjweofw9ae", "fjweofw9ae", "'")
                b_comments = comment_get(b_script, b_diff, "fjweofw9ae", "fjweofw9ae", "'")
            elif lang in langtype4: #xqueryタイプ
                a_comments = comment_get(a_script, a_diff, "(:", ":)", "fjweofw9ae")
                b_comments = comment_get(b_script, b_diff, "(:", ":)", "fjweofw9ae")
            else:
                raise RuntimeError #ここにきたらまずいのでエラーで一旦終わらせる
            
            path = dir_calc(proj_name, number) + 'diff_' + str(patch) + '_' + url_key + '.json'
            #a,bコメントの内容をファイルに一時保存は．．させない．
            #その後，コメントをdetectorに突っ込む
            #print "a_comments = " + str(a_comments)
            #print "b_comments = " + str(b_comments)
            if len(a_comments) >= 1:
                a_comments = detect(a_comments)
            else:
                a_comments = []
            print("a_SATDs = " + str(a_comments))

            if len(b_comments) >= 1:
                b_comments = detect(b_comments)
            else:
                b_comments = []
            print("b_SATDs = " + str(b_comments))

            result_dic = {"a_comments":a_comments, "b_comments":b_comments}
            #detectorを動かしたらもう一度保存．
            with open(path, 'w') as g:
                json.dump(result_dic, g, sort_keys=True)
        patch += 1
#もしかしたらunicode文字への変換処理が必要かもしれない．

print("finish!")



#パッチの数の取り方．．currentで取ってjsonに変換した後に値を取得しカウントダウン式に取る？

#レビューコメントの取り方
#while patch <= total_patch: #各パッチについてコメントとレビューの情報を取る
    #script = 'curl "https://'+ address +'/changes/' + str(number) + '/revisions/' + str(patch) + '/comments"'
