## 2021/05/09 ##

import re
import time
import json
import random
import requests

from bs4 import BeautifulSoup

# 保存输出结果的路径
FILE_DIR = 'E:/OneDrive/VSCode_Python/projects/20210509_NLP/materials/'
# 系统休眠时间的上下限
LOWER_BOUND = 0.5
HIGHER_BOUND = 1.0
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
    'getDoctReply': False,
    'getPageQuestion': False,
    'getTopicPages': False,
}


def requestPageHTML(url, encoding='utf-8', save_path=None):
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
    sleep_time = random.uniform(lhs, rhs) # 在上下限范围内随机选取休眠时间
    print('Sleep time: %.2lf | Sleeping...' % (sleep_time))
    print('------')
    time.sleep(sleep_time) # 系统休眠


def selectNodeByAttr(html, node, encoding='utf-8', attrs=None):
    # 构造bs4解析器
    parser = BeautifulSoup(html, "html.parser", from_encoding=encoding)

    # 根据传入的字符串获取页面中的所有目标节点
    nodes = parser.find_all(node, attrs=attrs)

    return nodes


def getDoctReply(html):

    relpy_dict = {} # 医生回复的字典
    # 选取当前话题下所有医生的回复
    doct_reply_divs = selectNodeByAttr(html, 'div', 'gbk',
                                     {'class': 'docall clearfix'}) # doct: doctor
    # 遍历每个回复
    for doct_reply_div in doct_reply_divs:

        info = {}
        doct_reply_html = str(doct_reply_div)

        # 由于函数selectNodeByAttr返回的结果是一个列表，同时单个doct_reply_div节点仅对应一位医生的回答，因此我们可以直接选取首元素，即返回值的[0]，作为目标值

        # 医生名字必定存在，但有一些普通医生可能姓名就是“医生”或“在职医师”
        doct_name = selectNodeByAttr(doct_reply_html, 'a', 'gbk',
                                     {'class': 'f14 fb Doc_bla'})[0]  

        # 医生回答必定存在
        doct_reply = selectNodeByAttr(
            doct_reply_html, 'div', 'gbk',
            {'class': 'pt15 f14 graydeep pl20 pr20 deepblue'})[0]
        info['回答'] = doct_reply.get_text().lstrip().rstrip()

        # 医生对应的职称、医院、科室、专长有一些医生没有这些属性，因此需要用try-except块来处理IndexError异常

        try:
            doct_title = selectNodeByAttr(doct_reply_html, 'span', 'gbk',
                                          {'class': 'fl ml10 btn-a mr5'})[0]
            info['职称'] = doct_title.get_text().split('：')[1].lstrip().rstrip()
        except IndexError:
            print("Doctor %s doesn't have 'title' attribute" %
                  (doct_name.get_text()))
            doct_title = None
            info['职称'] = None

        try:
            doct_hosp = selectNodeByAttr(doct_reply_html, 'span', 'gbk',
                                         {'class': '_hospital'})[0]
            info['医院'] = doct_hosp.get_text().lstrip().rstrip()
        except IndexError:
            print("Doctor %s doesn't have 'hospital' attribute" %
                  (doct_name.get_text()))
            doct_hosp = None
            info['医院'] = None

        try:
            doct_depart = selectNodeByAttr(doct_reply_html, 'span', 'gbk',
                                           {'class': '_depart'})[0]
            info['科室'] = doct_depart.get_text().lstrip().rstrip()
        except IndexError:
            print("Doctor %s doesn't have 'department' attribute" %
                  (doct_name.get_text()))
            doct_depart = None
            info['科室'] = None

        try:
            doct_spec = selectNodeByAttr(doct_reply_html, 'p', 'gbk',
                                         {'class': 'fl graydeep'})[0]
            info['专长'] = doct_spec.get_text().split('：')[1].lstrip().rstrip()
        except IndexError:
            print("Doctor %s doesn't have 'speciality' attribute" %
                  (doct_name.get_text()))
            doct_spec = None
            info['专长'] = None

        # 以医生的名字作为键，相关信息作为值构造字典
        relpy_dict[doct_name.get_text()] = info

    # FUNC_DEBUG_OUTPUT中对应项为True则输出调试信息
    if FUNC_DEBUG_OUTPUT['getDoctReply']:
        for key, val in relpy_dict.items():
            print(key)
            for k, v in val.items():
                print(k, ':', v)

    return relpy_dict


def getPageQuestion(html):

    question_dict = {}
    # 选取所有包含问题和描述的div
    question_and_description = selectNodeByAttr(
        html, 'div', 'utf-8', {'class': 'search-detail-con-new ant-pt4'})
    # 遍历当前页面的每个问答条目
    for div in question_and_description:
        try:
            # 选取包含信息的目标节点
            sub_a, sub_p = div.div.a, div.p

            # 对信息进行简单清洗
            question = sub_a.get_text()
            question = question.split('-')[0].rstrip().lstrip()

            description = sub_p.get_text()
            description = description.rstrip().lstrip()
            pos = description.find('详情>>')
            if pos != -1:
                description = description[0:pos].rstrip()
            else:
                print('Pattern string "详情>>" is not exists')
        # 有一部分其他非“有问必答”的条目处理时会抛出AttributeError异常，略过即可
        except AttributeError as err: 
            print('Error: %s' % err)
            continue

        try:
            # 请求问题的链接，获取页面html，并爬取医生的回复
            relpy_url = sub_a['href']
            relpy_html = requestPageHTML(relpy_url, 'gbk')
            relpy_dict = getDoctReply(relpy_html)

            # 将数据打包成字典
            question_dict[question] = [description, relpy_dict]
            systemSleep()
        except Exception:
            print('Exception')
            pass

    return question_dict


def getTopicPages(html, init_url, limit=10):
    search_res = selectNodeByAttr(
        html, 'div', 'utf-8',
        {'class': 'ant-pt20 ant-pb20 ant-yahei search-page'})

    for div in search_res:
        page_hrefs = selectNodeByAttr(html, 'a', 'utf-8', {'typeid': 'zhao'})
        for page_href in page_hrefs:
            # 提取出“尾页”对应的html节点，当知道了尾页，就知道了该关键词搜索结果总共有几页
            if page_href.get_text() == '尾页':
                num = re.search(r'\d+$', page_href['href'],
                                flags=0)  # 正则表达式匹配页数
                if num != None:  # 结果非空，说明匹配成功
                    num = int(str(num.group()))
                    print('Ending page number:', num)
                    num = min(limit, num)  # 控制爬取页数不要超过limit
                    print('Target page number:', num)
                    # 利用列表推导构造所有包含搜索结果的url
                    return [
                        init_url + '&page=' + str(num)
                        for num in range(1, num + 1)
                    ]
                else:  # 匹配失败，抛出异常
                    print('Ending page number no match!')
                    raise Exception


def unitTestOne():
    # 单元测试
    html = requestPageHTML(
        r'http://club.xywy.com/question/20151217/97058121.htm', 'gbk',
        FILE_DIR + 'test_reply.html')
    getDoctReply(html)


def crawl(xywy_url=None):
    # 必须传入一个非空URL
    if xywy_url == None:
        print("URL doesn't be transmitted, check again!")
        return

    # 保存每个页面问题字典的最终输出的列表
    question_dicts = []

    # 第一次查询，获取种子页面的html，后面将从这里面提取总页数
    seed_html = requestPageHTML(xywy_url, 'utf-8') # 传入FILE_DIR + 'test_page.html'作第三个参数可以保存测试页面

    # 获取当前话题下的总页数，并依次构造一组URL
    page_urls = getTopicPages(seed_html, xywy_url, 50)

    # 遍历获得的URL，从中提取问答信息
    for ii, page_url in enumerate(page_urls):

        print('Current URL: %s | Total URL number: %d' %
              (page_url, len(page_urls)))  # 打印调试信息：当前URL和URL总数

        curr_html = requestPageHTML(page_url, 'utf-8')  # 请求该页面

        question_dict = getPageQuestion(curr_html)  # 调用函数获取该页面的问题字典

        # 每处理完一个页面输出一次数据供参考
        print('Data output:')
        for key, val in question_dict.items():
            print('Question:', key)
            print('Detail information:')
            print(val)

        question_dicts.append(question_dict)  # 当前结果保存到最终列表中

        if ii % 5 == 0:  # 每隔5个页面保存一次中间结果
            with open(FILE_DIR + 'question_dict_%d.json' % ii,
                      'w',
                      encoding='utf-8') as fp:
                json_str = json.dumps(question_dicts, ensure_ascii=False)
                json_str.encode('utf-8')
                fp.write(json_str)

        systemSleep(0.5, 1.0) # 每爬取一次，系统暂停一段时间，防止被封ip

    # 最后进行一次输出，保存最终结果
    with open(FILE_DIR + 'question_dict_last.json' % ii, 'w',
              encoding='utf-8') as fp:
        json_str = json.dumps(question_dicts, ensure_ascii=False)
        json_str.encode('utf-8')
        fp.write(json_str)


if __name__ == '__main__':

    print('Start main...')

    search_keyword = '勃起'
    xywy_url = r'https://so.xywy.com/comse.php?keyword=' + search_keyword + '&src=so'

    crawl(xywy_url)
