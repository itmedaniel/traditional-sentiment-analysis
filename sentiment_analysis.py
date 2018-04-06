# -*- coding: utf-8 -*-
#
# Copyright @2017 R&D, CINS Inc. (cins.com)
#
# Author: dangzhengyang <dangzhengyang@gmail.com>
#

import sys
import os
import jieba
reload(sys)
sys.setdefaultencoding("utf-8")

def sentiment_score(sentence):
    content = segment(sentence, cut_all=False)
    stopwords_file = '../doc/stopwords.txt'
    emotion_file = '../doc/BosonNLP_sentiment_score.txt'
    not_file = '../doc/not_word.txt'
    adv_file = '../doc/adv_word.txt'
    emotion_dict = read_thesaurus(emotion_file)
    not_list = read_word(not_file)
    adv_dict = read_thesaurus(adv_file)
    sentence = remove_stopword(content, stopwords_file)
    sentence_score = compute_sentence_score(sentence, emotion_dict, not_list, adv_dict)

    print sentence_score
    return sentence_score

def segment(content, cut_all=False):
    #采用搜索模式进行分词
    delimiter = '\001'
    seg_list = jieba.cut(content, cut_all)
    content = delimiter.join(seg_list)
    return content

def remove_stopword(content, stopwords_file):
    #去停用词
    stop_words = read_word(stopwords_file)
    sentence = []
    for word in content:
        word  = word.encode('utf-8')
        if word not in stop_words:
            sentence.append(word)
    return sentence

def read_thesaurus(thesaurus_path):
    #导入情感词
    thesaurus_file = sys.stdin if thesaurus_path is None else open(thesaurus_path, 'rb')
    thesaurus_dict = {}
    for emotion_word in thesaurus_file.readlines():
        emotion_value = emotion_word.strip().split(' ')
        if len(emotion_value) == 2:
            thesaurus_dict[emotion_value[0]] = emotion_value[1]

    return thesaurus_dict

def read_word(word_path):
    #导入否定词
    file_file = sys.stdin if word_path is None else open(word_path, 'rb')
    return [word.strip() for word in file_file.readlines()]

def compute_sentence_score(sentence, emotion_dict, not_list, adv_dict):
    #计算句子情感得分
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
    if result_end_filename is not None and not os.path.isfile(data):
        print('The data does not exist:{0}.'.format(result_end_filename))
        return False

    emotion_file = kw.get('emotion_file', None)
    if emotion_file is not None and not os.path.isfile(data):
        print('The data does not exist:{0}.'.format(emotion_file))
        return False

    not_file = kw.get('not_file', None)
    if not_file is not None and not os.path.isfile(data):
        print('The data does not exist:{0}.'.format(not_file))
        return False

    adv_file = kw.get('adv_file', None)
    if adv_file is not None and not os.path.isfile(data):
        print('The data does not exist:{0}.'.format(adv_file))
        return False

    return True


if __name__ == "__main__":
    # sentence = "当年山奴亚国王为了听故事的结尾，就把杀山鲁佐德的日期延迟了一天又一天。宰相的山鲁佐德每天讲一个故事，她的故事无穷无尽，一个比一个精彩，一直讲到第一千零一夜，终于感动了国王。山努亚说：凭安拉的名义起誓，我决心不杀你了，你的故事让我感动。我将把这些故事记录下来，永远保存。”如今有故事的人快到一千个了，有故事的人作为一个世间百态的平台，你可以从中看到尘世间芸芸众生的沸腾挣扎，为了七情六欲而奋力拼搏，收获几缕风光，大部分时候还是吃一嘴灰，真无奈啊。谁都渴望奇迹发生，就像山鲁佐德在一千个夜里的祈祷，西西弗斯渴望石头伫立在山顶，我们都希望生命中的故事不会变成事故，每天都凝固在美好发生的一瞬间，为此我们日夜努力不停息，就为了一千个日夜后，能够看见更坚硬的土地和更美好的自己。"
    sentence = "潜心在事业上的人都是孤独的，妥协于世俗又不愿意刻意逢迎的德永，坚守自己却迷失其中得不到认同的神谷，拼尽全力，热血的梦想最多可能点燃的只有刹那的火花，不过大概人活着就不会有太差的结局吧。喜欢各种大全景下小人物透出的疏离感和孤独感，谢幕演出非常精彩，这部镜头语言真丰富，演员表演很棒。"
    sentiment_score(sentence)


