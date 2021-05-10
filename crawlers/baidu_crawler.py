## 2021/05/10 ##

import re
import time
import json
import random
import requests
import unicodedata

from bs4 import BeautifulSoup

# 保存输出结果的路径
FILE_DIR = 'E:/OneDrive/VSCode_Python/projects/20210509_NLP/materials/'
# 系统休眠时间的上下限
LOWER_BOUND = 0.5
HIGHER_BOUND = 1.0
# 百度百科查询链接
BAIKE_URL = r'https://baike.baidu.com'
# 请求头
HEADERS = {
    'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0'
}

# 控制函数是否打印中间结果
FUNC_DEBUG_OUTPUT = {
    'requestPageHTML': False,
    'systemSleep': False,
    'selectNodeByAttr': False,
    'getItemCoreMsg': True,
    'crawl': True,
    'main': True,
}


def requestPageHTML(url, encoding='utf-8', save_path=None):
    # 必须传入一个非空URL
    if url == None:
        print("'requestPageHTML': URL doesn't be transmitted, check again!")
        return

    # 根据保存路径的有无确定是否需要存储文件到本地
    if save_path != None:
        fp = open(save_path, 'w', encoding=encoding)  # 输出文件
    elif save_path == None:
        pass

    # 通过request.get方法请求网站
    res = requests.get(
        url, headers=HEADERS)  # requests模块会自动解码来自服务器的内容，可以使用res.encoding来查看编码

    # 如果网页原始编码与目标编码不统一，则将编码转换为传入的编码
    if res.encoding == encoding:
        print('Page encoding: %s' % (res.encoding))  # 页面使用的编码
    if res.encoding != encoding:
        print('Page encoding transforming: %s -> %s' %
              (res.encoding, encoding))
        res.encoding = encoding

    html = res.text  # 提取网页的html编码

    if save_path != None:
        fp.write(html)
        fp.close()

    return html


def systemSleep(lhs=LOWER_BOUND, rhs=HIGHER_BOUND):
    sleep_time = random.uniform(lhs, rhs)  # 在上下限范围内随机选取休眠时间
    print('Sleep time: %.2lf | Sleeping...' % (sleep_time))
    print('------')
    time.sleep(sleep_time)  # 系统休眠


def selectNodeByAttr(html, node, encoding='utf-8', attrs=None):
    # 构造bs4解析器
    parser = BeautifulSoup(html, "html.parser", from_encoding=encoding)

    # 根据传入的字符串获取页面中的所有目标节点
    nodes = parser.find_all(node, attrs=attrs)

    return nodes


def getItemCoreMsg(html):
    encoding = 'utf-8'  # 该函数中使用的编码

    item_dict = {}

    # 选取出包含了所有信息的节点，即divs
    divs = selectNodeByAttr(html, 'div', encoding)

    # 三类信息对应的参数，构造成一个列表
    argus = [
        [str(divs), 'dd', encoding, {
            'class': 'lemmaWgt-lemmaTitle-title'
        }],  # 条目关键词
        [
            str(divs), 'div', encoding, {
                'class': 'lemma-summary',
                'label-module': 'lemmaSummary'
            }
        ],  # 条目简介
        [
            str(divs), 'div', encoding, {
                'class': ['dl-baseinfo', "basic-info cmn-clearfix"]
            }
        ],  # 条目附加信息
    ]

    infos = []  # 存储三类信息对应的HTML文本的列表
    # 循环获取信息
    for argu in argus:
        try:
            info = selectNodeByAttr(argu[0], argu[1], argu[2], argu[3])
        except IndexError:
            info = None
        finally:
            infos.append(info)

    title = ''
    desc_paras = []  # 保存条目中段落的列表
    pair_dict = {}

    try:
        # 提取条目关键词
        title = infos[0][0].h1.get_text()

        # 提取条目简介
        desc_divs = selectNodeByAttr(str(infos[1][0]), 'div', encoding, {
            'class': 'para',
            'label-module': 'para'
        })  # 选取条目中的每个段落

        # 循环获取条目中段落
        for desc_div in desc_divs:
            desc_paras.append(desc_div.get_text().lstrip().rstrip())

        # TODO: 根据infos[1]提取出文本中的链接
        text_hrefs = selectNodeByAttr(str(infos[1][0]), 'a', encoding,
                                      {'target': '_blank'})
        for text_href in text_hrefs:
            text = text_href.get_text()
            href = BAIKE_URL + text_href['href']
            # print(text)
            # print(href)

        # 提取条目附加信息

        for div in infos[2]:
            #print(div)
            #print('div -----')
            # pairs = selectNodeByAttr(str(div), 'dl',
            #                          encoding)  # 找出包含了条目附加信息的节点
            keys = selectNodeByAttr(str(div), 'dt', encoding)
            vals = selectNodeByAttr(str(div), 'dd', encoding)
            # print(pairs)
            for key, val in zip(keys, vals):
                # 键为dt节点，值为dd节点
                key = unicodedata.normalize('NFKC', key.get_text())
                val = unicodedata.normalize('NFKC',
                                            val.get_text().lstrip().rstrip())
                pair_dict[key] = val
            #print('pairs ------')

        if FUNC_DEBUG_OUTPUT['getItemCoreMsg']:
            print(title)
            print(desc_paras)
            print(pair_dict)

    except IndexError as err:
        print('Exception: %s', err)

    item_dict[title] = [desc_paras, pair_dict]
    return item_dict


def getItemCoreMsgUnitTest(baidu_url=None):
    # 必须传入一个非空URL
    if baidu_url == None:
        print("'getItemCoreMsgUnitTest': URL doesn't be transmitted, check again!")
        return
        
    html = requestPageHTML(baidu_url, 'utf-8',
                           FILE_DIR + 'test_page_baidu.html')
    getItemCoreMsg(html)


def crawl(baidu_url=None):
    # 必须传入一个非空URL
    if baidu_url == None:
        print("'crawl': URL doesn't be transmitted, check again!")
        return

    # 第一次查询，获取种子页面的html
    seed_html = requestPageHTML(
        baidu_url, 'utf-8', FILE_DIR +
        'test_page_baidu.html')  # 传入FILE_DIR + 'test_page.html'作第三个参数可以保存测试页面


def tvsKeywords(base_url, keywords=None):
    # 必须传入一个非空URL
    if baidu_url == None:
        print("'tvsKeywords': URL doesn't be transmitted, check again!")
        return

    item_dicts = []  # 保存爬取的查询结果的列表
    baidu_urls = [(base_url + keyword) for keyword in keywords]  # 构造查询URL列表
    for baidu_url in baidu_urls:
        html = requestPageHTML(baidu_url)  # 获取网页HTML文档
        item_dict = getItemCoreMsg(html)  # 提取信息构造字典
        item_dicts.append(item_dict)  # 存储字典到列表中
    return item_dicts


if __name__ == '__main__':

    print('Start main...')

    base_url = r'https://baike.baidu.com/item/'
    disease_keywords = ['脑瘫', '脑卒中', '白血病', '肺癌', '胃癌', '口腔癌']
    medicine_keywords = [
        '洛伐他汀', '利多卡因', '普鲁卡因', '奥美拉唑', '克林霉素', '左氧氟沙星', '艾普拉唑', '西咪替丁'
    ]
    item_dicts = tvsKeywords(base_url, medicine_keywords) # 遍历每个关键字进行查询

    # 打开文件进行写入
    with open(FILE_DIR + 'item_dicts.json', 'w', encoding='utf-8') as fp:
        json_str = json.dumps(item_dicts, ensure_ascii=False)
        json_str.encode('utf-8')
        fp.write(json_str)