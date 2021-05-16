#!/usr/bin/env python3

# 2021/05/16 #

import re
import json
import random
import chardet
import pymongo
import requests
import threading

import urllib.request
import urllib.parse

from lxml import etree


class XYWYSymptomSpider:
    '''基于寻医问药网的医学数据采集'''
    def __init__(self):
        # 一些预定义的变量
        self.file_dir = 'E:/OneDrive/VSCode_Python/projects/20210509_NLP/missing_pages/'
        self.attrs = ['jieshao', 'yuanyin', 'yufang', 'jiancha', 'zhenduan']
        self.agent = [
            'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
            'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0',
            'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)',
            'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
            'Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
            'Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11',
            'Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Maxthon 2.0)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; The World)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SE 2.X MetaSr 1.0; SE 2.X MetaSr 1.0; .NET CLR 2.0.50727; SE 2.X MetaSr 1.0)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
        ]

        # 初始化数据库
        self.conn = pymongo.MongoClient(host='localhost')
        self.db = self.conn['medical']
        self.col_symp = self.db['symptom_test']
        # self.col_symp.delete_many({})  # 插入之前先清除集合中所有内容，要视需要开启

    '''根据url，请求html'''

    def get_html(self, url, encoding='utf-8'):
        headers = {'User-Agent': random.sample(self.agent, 1)[0]}  # 随机选取U-A头
        res = requests.get(url, headers=headers)
        html = res.text.encode(encoding)

        return html

    '''url解析'''

    def spider_main(self, pages=None, thread_id=1):
        err_pages = []
        for page in pages:
            try:
                page_url = r'http://zzk.xywy.com/p/%s.html' % page

                page_items = self.symptom_spider(page_url)  # 传回当前页面药品信息列表

                print('thread: %s | index: %s | url: %s' %
                      (thread_id, page, page_url))  # 打印线程信息

            except Exception as e:
                err_pages.append(page)
                print(e, page)
        return err_pages

    '''药品信息解析'''

    def symptom_spider(self, url):
        html = self.get_html(url, 'ISO8859-1')  # 页面采用的是'ISO8859-1'编码，其他编码可能会报错
        selector = etree.HTML(html)

        names = selector.xpath(
            '//ul[starts-with(@class,"ks-zm-list clearfix")]/li/a/@title'
        )  # 症状名
        hrefs = selector.xpath(
            '//ul[starts-with(@class,"ks-zm-list clearfix")]/li/a/@href'
        )  # 症状详情链接，包含了症状对应的数字id

        # 打包信息
        page_items = []
        for ind, (name, href) in enumerate(zip(names, hrefs)):
            item = {}
            item['name'] = name
            item['url'] = url
            item['href'] = href
            item['page_index'] = ind
            item['source'] = '寻医问药网'
            item['refer'] = 'symptom'
            page_items.append(item)
            print(item)

        self.detail_spider(page_items)  # 爬取症状的详细信息

        # 爬取完成后，结果插入数据库（这里也可以用insert_many代替for循环）
        for item in page_items:
            self.col_symp.insert_one(item)

        return page_items

    def detail_spider(self, items):

        base_url = 'http://zzk.xywy.com/'
        for item in items:
            # 根据条目对应的数字id和基准url，构造需要访问的五个页面url
            item_num = re.search(r'\d+', item['href'], flags=0).group()
            target_urls = [
                ''.join([base_url, str(item_num), '_', attr, '.html'])
                for attr in self.attrs
            ]

            try:  # 有时候会报网络连接的错误，这里需要用try-except块进行处理
                for ii, target_url in enumerate(target_urls):
                    html = self.get_html(target_url, 'ISO8859-1')
                    selector = etree.HTML(html)

                    paras = []
                    if self.attrs[ii] == 'jiancha':  # 检查页面的HTML结构与其他页面不一致，单独处理
                        paras = selector.xpath(
                            '//div[starts-with(@class,"zz-articl-con mt15")]/p/text()'
                        )
                    else:
                        paras = selector.xpath(
                            '//div[starts-with(@class,"zz-articl fr f14")]/p/text()'
                        )

                    # 文本处理
                    text = ''
                    if len(paras) == 1:
                        text = paras[0].lstrip().rstrip()
                    else:
                        paras = [para.lstrip().rstrip() for para in paras]
                        text = '\n'.join(paras)

                    item[self.attrs[ii]] = text

                print('Current item: %s' % (item['name']))
            except Exception as e:
                print(e, item['name'])
                pass
            finally:
                continue


class myThread(threading.Thread):  #继承父类threading.Thread
    def __init__(self,
                 thread_id,
                 name,
                 spider_handler=None,
                 handle_range=None):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.name = name
        self.spider_handler = spider_handler
        self.handle_range = handle_range

    def run(self):  #把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        print("Starting", self.name)

        err_pages = self.spider_handler.spider_main(self.handle_range,
                                                    self.thread_id)

        with open(self.spider_handler.file_dir + 'symptom_err_pages.json',
                  'a',
                  encoding='utf-8') as fp:
            json_str = json.dumps(err_pages, ensure_ascii=False, indent=4)
            json_str.encode('utf-8')
            fp.write(json_str)

        print("Exiting", self.name)


if __name__ == '__main__':
    print('-- Main Started --')

    opt = 1  # 这个网站用多线程爬取会出错，只能选用单线程方式爬取

    if opt == 0:  # 多线程抓取数据
        thread1 = myThread(1, "Thread-1", XYWYSymptomSpider(),
                           [chr(i) for i in range(97, 97 + 8)])
        thread2 = myThread(2, "Thread-2", XYWYSymptomSpider(),
                           [chr(i) for i in range(97 + 8, 97 + 16)])
        thread3 = myThread(3, "Thread-3", XYWYSymptomSpider(),
                           [chr(i) for i in range(97 + 16, 123)])

        thread1.start()
        thread2.start()
        thread3.start()
    elif opt == 1:  #单线程抓取数据
        XYWYSymptomSpider().spider_main([chr(i) for i in range(97, 123)], 1)

    print('-- Main Finished --')
