#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright @2017 R&D, CINS Inc. (cins.com)
#
# Author: dangzhengyang <dangzhengyang@gmail.com>
#

import sys
import os
reload(sys)
sys.path.append('/usr/local/lib/python2.7/site-packages/')
sys.path.append('/root/anaconda/lib/python2.7/site-packages/')
import settings
from optparse import OptionParser
import jieba
import time
sys.setdefaultencoding("utf-8")

def load_comment_list(data, delimiter):
    #加载评论
    comment_list = [line.strip().split(delimiter) for line in open(data).readlines()]
    return comment_list

def segment(content, delimiter, cut_all=False):
    #采用搜索模式进行分词
    seg_list = jieba.cut(content, cut_all)
    content = delimiter.join(seg_list)
    return content

def extract_cluster_event_url(result_end_file, delimiter):
    #抽取主要事件的url，用于匹配与事件相对应的评论，丢弃与事件不相对应的评论

    cluster_file = sys.stdin if result_end_file is None else open(result_end_file, 'rb')

    all_cluster_event_list = []
    unique_cluster_event_url = []
    for cluster in cluster_file.readlines():
        cluster_event_list = cluster.strip().split('###')
        cluster_first_event_url = cluster_event_list[0].strip().split(delimiter)[0]
        same_event_url = []
        for cluster_event in cluster_event_list[1:len(cluster_event_list)-1]:
            cluster_event_to_end_url = cluster_event.strip().split(':::')[0]
            same_event_url.append(cluster_event_to_end_url)
        same_event_url.insert(0, cluster_first_event_url)
        all_cluster_event_list = all_cluster_event_list + same_event_url
        unique_cluster_event_url.append(same_event_url)

    return all_cluster_event_list, unique_cluster_event_url

def read_thesaurus(thesaurus_path):
    #导入情感词
    thesaurus_file = sys.stdin if thesaurus_path is None else open(thesaurus_path, 'rb')
    thesaurus_dict = {}
    for emotion_word in thesaurus_file.readlines():
        emotion_value = emotion_word.strip().split(' ')
        if len(emotion_value) == 2:
            thesaurus_dict[emotion_value[0]] = emotion_value[1]

    return thesaurus_dict

def read_not_word(not_path):
    #导入否定词
    not_file = sys.stdin if not_path is None else open(not_path, 'rb')
    return [word.strip() for word in not_file.readlines()]

def compute_sentence_score(sentence, emotion_dict, not_list, adv_dict):
    #计算句子情感得分
    sentence = sentence.strip().split(' ')
    sentence_score = 0.0
    word_counter = 0
    level = 6.53951977886#最大值与最小值的一半
    for word in sentence:
        current_word = word
        current_word_position = sentence.index(current_word)
        if emotion_dict.has_key(current_word):
            word_score = float(emotion_dict[current_word])
            if word_score > 0:
                if current_word_position != 0 and current_word_position != len(sentence) - 1:
                    front_word = sentence[current_word_position - 1]
                    back_word = sentence[current_word_position + 1]
                    if adv_dict.has_key(front_word):
                        word_score *= float(adv_dict[front_word])
                    elif front_word in not_list:
                        word_score *= -1
                    elif emotion_dict.has_key(front_word) and float(emotion_dict[front_word]) < 0:
                        word_score *= -1
                    elif emotion_dict.has_key(back_word) and float(emotion_dict[back_word]) < 0:
                        word_score *= -1
                    else:
                        pass
                elif current_word_position == 0 and current_word_position != len(sentence) - 1:
                    back_word = sentence[current_word_position + 1]
                    if emotion_dict.has_key(back_word) and float(emotion_dict[back_word]) < 0:
                        word_score *= -1
                    else:
                        pass
                elif current_word_position != 0 and current_word_position == len(sentence) - 1:
                    front_word = sentence[current_word_position - 1]
                    if adv_dict.has_key(front_word):
                        word_score *= float(adv_dict[front_word])
                    elif front_word in not_list:
                        word_score *= -1
                    elif emotion_dict.has_key(front_word) and float(emotion_dict[front_word]) < 0:
                        word_score *= -1
                    else:
                        pass
                else:
                    pass
            elif word_score < 0:
                if current_word_position != 0:
                    front_word = sentence[current_word_position - 1]
                    if adv_dict.has_key(front_word):
                        word_score *= float(adv_dict[front_word])
                    elif front_word in not_list:
                        word_score *= -1
                    else:
                        pass
                else:
                    pass
            else:
                pass
        elif current_word in not_list:
            word_score = -0.5
        else:
            continue
        sentence_score += word_score
        word_counter += 1

    if word_counter == 0:
        sentence_score = 0.0
    else:
        sentence_score = sentence_score / word_counter / level
    if sentence_score >= 1.0:
        sentence_score = 1.0
    elif sentence_score <= -1.0:
        sentence_score = -1.0
    else:
        pass
    return sentence_score

def getfilenames(path):
    return os.listdir(path)

def read_input(fr,delimiter):#贴吧、新闻
    for event in fr:
        yield event.strip().split(delimiter)

def check_parameters(**kw):
    '''Check whether the parameters safy the conditions
     Arga:
         delimiter:The delimiter between columns
         indexes:A array of indexes of the uuid and content and title(Optional)
         data:The filename of the data
    '''
    delimiter = kw.get('delimiter', None)
    if delimiter is None:
        msg = [
            "The delimiter is required."
            "Use '-s' in console mode or 'delimiter=' in func call to set it"
            ]
        print("{0}".format('\n'.join(msg)))
        return False

    data = kw.get('data', None)
    if data is not None and not os.path.isfile(data):
        print('The data does not exist:{0}.'.format(data))
        return False
    
    result_end_filename = kw.get('result_end_filename', None)
    if result_end_filename is not None and not os.path.isfile(result_end_filename):
        print('The result_end_filename does not exist:{0}.'.format(result_end_filename))
        return False

    emotion_file = kw.get('emotion_file', None)
    if emotion_file is not None and not os.path.isfile(emotion_file):
        print('The emotion_file does not exist:{0}.'.format(emotion_file))
        return False

    not_file = kw.get('not_file', None)
    if not_file is not None and not os.path.isfile(not_file):
        print('The not_file does not exist:{0}.'.format(not_file))
        return False

    adv_file = kw.get('adv_file', None)
    if adv_file is not None and not os.path.isfile(adv_file):
        print('The adv_file does not exist:{0}.'.format(adv_file))
        return False

    cluster_file = kw.get('cluster_file', None)
    if cluster_file is not None and not os.path.isfile(cluster_file):
        print('The cluster_file does not exist:{0}.'.format(cluster_file))
        return False

    return True

def main(**kw):
    if not check_parameters(**kw):
        return False

    data = kw['data']
    delimiter = kw['delimiter']
    out = kw.get('out', None)
    emotion_path = kw.get('emotion_path')#情感文件
    result_end_path = kw.get('result_end_path')#聚集文件
    not_path = kw.get('not_path')#否定词文件
    adv_path = kw.get('adv_path')#程度副词文件

    print 'start'
    start_time = time.clock()
    delimiter = settings.FIELD_DELIMITER[delimiter] if delimiter in settings.FIELD_DELIMITER.keys() else delimiter

    emotion_dict = read_thesaurus(emotion_path)
    not_list = read_not_word(not_path)
    adv_dict = read_thesaurus(adv_path)
    all_cluster_event_list, unique_cluster_event_url = extract_cluster_event_url(result_end_path, delimiter)

    stdin = sys.stdin if data is None else open(data, 'rb')
    stdout = sys.stdout if out is None else open(out, 'wb')

    for comment in read_input(stdin, delimiter):

        comment_uuid = comment[6]#评论uuid
        url = comment[0]#评论url
        new_url = url.replace(comment_uuid, '')
        if new_url not in all_cluster_event_list:
            continue
        for url_list in unique_cluster_event_url:
            if new_url in url_list:
                new_url = url_list[0]

        rm_comment_content = comment[9]#评论内容
        if len(rm_comment_content) <=10:
            continue

        comment_time = comment[7]#评论时间
        comment_up_vote = comment[11]#评论点赞人数
        comment_content = comment[12]
        comment_score = compute_sentence_score(rm_comment_content, emotion_dict, not_list, adv_dict)#评论情感得分

        item = [new_url, comment_time, comment_content, str(comment_up_vote), str(comment_score)]
        stdout.write("{0}\n".format(delimiter.join(item)))

    end_time = time.clock()
    print end_time - start_time#消耗时间计时

    if data is not None:
        stdin.close()
    if out is not None:
        stdout.close()

    return True

if __name__ == "__main__":

    parser = OptionParser(usage="%prog -s delimiter -d data -z self_dict -o out -e emotion -t stopwords")

    parser.add_option(
        "-s", "--delimiter",
        help=u"The delimiter between columns, like \001"
    )

    parser.add_option(
        "-d", "--data",
        help=u"The file name of the data to be extracted(includes the full path)"
    ) 
    
    parser.add_option(
        "-o", "--out",
        help=u"The file name of the results(includes the full path)"
    )

    parser.add_option(
        "-r", "--result_end_path",
        help=u"The path of the result_end_file"
    )

    parser.add_option(
        "-e", "--emotion_path",
        help=u"The path of the emotion_file"
    )

    parser.add_option(
        "-n", "--not_path",
        help=u"The path of the not_file"
    )

    parser.add_option(
        "-a", "--adv_path",
        help=u"The path of the adv_file"
    )

    if not sys.argv[1:]:
        parser.print_help()
        exit(1)

    (opts, args) = parser.parse_args()
    main(delimiter=opts.delimiter, data=opts.data, out=opts.out, result_end_path=opts.result_end_path, emotion_path=opts.emotion_path, not_path=opts.not_path, adv_path=opts.adv_path)






