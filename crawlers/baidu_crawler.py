
## 2021/05/10 ##

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

if __name__ == '__main__':
    pass