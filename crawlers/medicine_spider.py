#!/usr/bin/env python3

# 2021/05/12 #

import urllib.request
import urllib.parse
import pymongo
import threading
import json
import re

from lxml import etree


class XYWYMedicineSpider:
    '''基于寻医问药网的医学数据采集'''
    def __init__(self):
        # 初始化数据库
        self.conn = pymongo.MongoClient(host='localhost')

        self.db = self.conn['medical']

        self.col_med = self.db['medicine']

        self.col_med.delete_many({})

        self.file_dir = 'E:/OneDrive/VSCode_Python/projects/20210509_NLP/missing_pages/'

    '''根据url，请求html'''

    def get_html(self, url):
        headers = {
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/51.0.2704.63 Safari/537.36'
        }
        req = urllib.request.Request(url=url, headers=headers)
        res = urllib.request.urlopen(req)
        html = res.read().decode('utf-8')
        return html

    '''url解析'''

    def spider_main(self, pages=None, thread_id=1):
        err_pages = []
        for page in pages:
            # try:
                page_url = r'http://yao.xywy.com/class/4-0-0-1-0-%s.htm' % page

                page_items = self.medicine_spider(page_url)  # 传回当前页面药品信息列表
                # 遍历列表逐行插入
                for item in page_items:
                    item['url'] = page_url
                    self.col_med.insert_one(item)

                print('thread: %s | index: %s | url: %s' %
                      (thread_id, page, page_url))

            # except Exception as e:
            #     err_pages.append(page)
            #     print(e, page)
        return err_pages

    '''药品信息解析'''

    def medicine_spider(self, url):
        html = self.get_html(url)
        selector = etree.HTML(html)
        names = selector.xpath(
            '//div[@class="h-drugs-item"]/div[@class="h-drugs-hd clearfix"]/a'
        )  # 药品名
        efficacys = selector.xpath(
            '//div[@class="h-drugs-item"]/div[@class="h-drugs-con clearfix"]/div[@class="fl h-drugs-txt ml20"]/div[@class="fl"]'
        )  # 药品功能简介

        # 打包药品信息
        page_items = []
        for ind, (name, efficacy) in enumerate(zip(names, efficacys)):
            item = {}
            item['page_index'] = ind
            item['name'] = name.text
            item['efficacy'] = efficacy.text
            page_items.append(item)

        return page_items

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

        with open(self.spider_handler.file_dir + 'medicine_err_pages.json',
                  'a',
                  encoding='utf-8') as fp:
            json_str = json.dumps(err_pages, ensure_ascii=False, indent=4)
            json_str.encode('utf-8')
            fp.write(json_str)

        print("Exiting", self.name)


if __name__ == '__main__':
    print('-- Main Started --')
    thread1 = myThread(1, "Thread-1", XYWYMedicineSpider(), range(1, 120))
    thread2 = myThread(2, "Thread-2", XYWYMedicineSpider(), range(120, 240))
    thread3 = myThread(3, "Thread-3", XYWYMedicineSpider(), range(240, 366))
    thread1.start()
    thread2.start()
    thread3.start()
    print('-- Main Finished --')
