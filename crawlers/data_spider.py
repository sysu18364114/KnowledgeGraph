#!/usr/bin/env python3

# 2021/05/12 #

import urllib.request
import urllib.parse
from lxml import etree
import pymongo
import threading
import time
import json
import re


class XYWYSpider:
    '''基于寻医问药网的医学数据采集'''
    def __init__(self):
        # 初始化数据库
        self.conn = pymongo.MongoClient(host='localhost')

        self.db = self.conn['medical']

        self.col_data = self.db['data']
        self.col_html = self.db['html']
        self.col_jc = self.db['jc']

        self.col_data.delete_many({})
        self.col_html.delete_many({})
        self.col_jc.delete_many({})

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
        html = res.read().decode('gbk')
        return html

    '''url解析'''

    # def url_parser(self, content):
    #     selector = etree.HTML(content)
    #     urls = [
    #         'http://www.anliguan.com' + i
    #         for i in selector.xpath('//h2[@class="item-title"]/a/@href')
    #     ]
    #     return urls
    '''抓取数据'''

    def spider_main(self, pages, thread_id=1):
        err_pages = []
        for page in pages:  # 后一个值表示目标爬取页面的标号列表
            try:
                basic_url = 'http://jib.xywy.com/il_sii/gaishu/%s.htm' % page
                cause_url = 'http://jib.xywy.com/il_sii/cause/%s.htm' % page
                prevent_url = 'http://jib.xywy.com/il_sii/prevent/%s.htm' % page
                symptom_url = 'http://jib.xywy.com/il_sii/symptom/%s.htm' % page
                inspect_url = 'http://jib.xywy.com/il_sii/inspect/%s.htm' % page
                treat_url = 'http://jib.xywy.com/il_sii/treat/%s.htm' % page
                food_url = 'http://jib.xywy.com/il_sii/food/%s.htm' % page
                drug_url = 'http://jib.xywy.com/il_sii/drug/%s.htm' % page

                data = {}
                data['url'] = basic_url
                data['basic_info'] = self.basicinfo_spider(basic_url)
                data['cause_info'] = self.common_spider(cause_url)
                data['prevent_info'] = self.common_spider(prevent_url)
                data['symptom_info'] = self.symptom_spider(symptom_url)
                data['inspect_info'] = self.inspect_spider(inspect_url)
                data['treat_info'] = self.treat_spider(treat_url)
                data['food_info'] = self.food_spider(food_url)
                data['drug_info'] = self.drug_spider(drug_url)

                print('thread: %s | index: %s | url: %s' %
                      (thread_id, page, basic_url))

                self.col_data.insert_one(data)
            except Exception as e:
                err_pages.append(page)
                print(e, page)
        return err_pages

    '''基本信息解析'''

    def basicinfo_spider(self, url):
        html = self.get_html(url)

        # 保存url和html信息到数据库
        data = {}
        data['url'] = url
        data['html'] = html
        self.col_html.insert_one(data)

        selector = etree.HTML(html)
        title = selector.xpath('//title/text()')[0]
        category = selector.xpath('//div[@class="wrap mt10 nav-bar"]/a/text()')
        desc = selector.xpath(
            '//div[@class="jib-articl-con jib-lh-articl"]/p/text()')
        ps = selector.xpath('//div[@class="mt20 articl-know"]/p')
        infobox = []
        for p in ps:
            info = p.xpath('string(.)').replace('\r', '').replace(
                '\n', '').replace('\xa0', '').replace('   ',
                                                      '').replace('\t', '')
            infobox.append(info)
        basic_data = {}
        basic_data['category'] = category
        basic_data['name'] = title.split('的简介')[0]
        basic_data['desc'] = desc
        basic_data['attributes'] = infobox
        return basic_data

    '''treat_infobox治疗解析'''

    def treat_spider(self, url):
        html = self.get_html(url)
        selector = etree.HTML(html)
        ps = selector.xpath('//div[starts-with(@class,"mt20 articl-know")]/p')
        infobox = []
        for p in ps:
            info = p.xpath('string(.)').replace('\r', '').replace(
                '\n', '').replace('\xa0', '').replace('   ',
                                                      '').replace('\t', '')
            infobox.append(info)
        return infobox

    '''treat_infobox治疗解析'''

    def drug_spider(self, url):
        html = self.get_html(url)
        selector = etree.HTML(html)
        drugs = [
            i.replace('\n', '').replace('\t', '').replace(' ', '') for i in
            selector.xpath('//div[@class="fl drug-pic-rec mr30"]/p/a/text()')
        ]
        return drugs

    '''food治疗解析'''

    def food_spider(self, url):
        html = self.get_html(url)
        selector = etree.HTML(html)
        divs = selector.xpath('//div[@class="diet-img clearfix mt20"]')
        try:
            food_data = {}
            food_data['good'] = divs[0].xpath('./div/p/text()')
            food_data['bad'] = divs[1].xpath('./div/p/text()')
            food_data['recommand'] = divs[2].xpath('./div/p/text()')
        except:
            return {}

        return food_data

    '''症状信息解析'''

    def symptom_spider(self, url):
        html = self.get_html(url)
        selector = etree.HTML(html)
        symptoms = selector.xpath('//a[@class="gre" ]/text()')
        ps = selector.xpath('//p')
        detail = []
        for p in ps:
            info = p.xpath('string(.)').replace('\r', '').replace(
                '\n', '').replace('\xa0', '').replace('   ',
                                                      '').replace('\t', '')
            detail.append(info)
        symptoms_data = {}
        symptoms_data['symptoms'] = symptoms
        symptoms_data['symptoms_detail'] = detail
        return symptoms, detail

    '''检查信息解析'''

    def inspect_spider(self, url):
        html = self.get_html(url)
        selector = etree.HTML(html)
        inspects = selector.xpath('//li[@class="check-item"]/a/@href')
        return inspects

    '''通用解析模块'''

    def common_spider(self, url):
        html = self.get_html(url)
        selector = etree.HTML(html)
        ps = selector.xpath('//p')
        infobox = []
        for p in ps:
            info = p.xpath('string(.)').replace('\r', '').replace(
                '\n', '').replace('\xa0', '').replace('   ',
                                                      '').replace('\t', '')
            if info:
                infobox.append(info)
        return '\n'.join(infobox)

    '''检查项抓取模块'''

    def inspect_crawl(self):
        for page in range(1, 3685):
            try:
                url = 'http://jck.xywy.com/jc_%s.html' % (page)
                html = self.get_html(url)
                data = {}
                data['url'] = url
                data['html'] = html
                self.col_jc.insert_one(data)
                print(url)
            except Exception as e:
                print(e)


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

        with open(self.spider_handler.file_dir + 'err_pages.json',
                  'a',
                  encoding='gbk') as fp:
            json_str = json.dumps(err_pages, ensure_ascii=False, indent=4)
            json_str.encode('gbk')
            fp.write(json_str)

        print("Exiting", self.name)


if __name__ == '__main__':

    print('-- Main Started --')

    # 多线程抓取数据
    thread1 = myThread(1, "Thread-1", XYWYSpider(), range(1, 2000))
    thread2 = myThread(2, "Thread-2", XYWYSpider(), range(2000, 4000))
    thread3 = myThread(3, "Thread-3", XYWYSpider(), range(4000, 6000))
    thread4 = myThread(4, "Thread-4", XYWYSpider(), range(6000, 8000))
    thread5 = myThread(5, "Thread-5", XYWYSpider(), range(8000, 11000))
    
    thread1.start()
    thread2.start()
    thread3.start()
    thread4.start()
    thread5.start()

    print('-- Main Finished --')
