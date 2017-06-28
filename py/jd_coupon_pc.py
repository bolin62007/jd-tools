# -*- coding: utf-8 -*-

import bs4
import requests
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()
import os
import time
import datetime
import json
import random
import math
import logging, logging.handlers
import argparse
import multiprocessing
from jd_wrapper import JDWrapper
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

# get function name
FuncName = lambda n=0: sys._getframe(n + 1).f_code.co_name

class JDCoupon(JDWrapper):
    '''
    This class used to click JD coupon
    '''
    duration = 5
    coupon_url = ""
    def setup(self, key, role_id):
        self.coupon_url = "http://coupon.jd.com/ilink/couponSendFront/send_index.action?key="+key+"&roleId="+role_id+"&to=www.jd.com"
    def click(self, level=None):
        try:
            resp = self.sess.get(self.coupon_url, timeout=5)
            if level != None:
                soup = bs4.BeautifulSoup(resp.text, "html.parser")
                tag1 = soup.select('title')
                tag2 = soup.select('div.content')
                if len(tag2):
                    logging.log(level, u'{}'.format(tag2[0].text.strip(' \t\r\n')))
                else:
                    if len(tag1):
                        logging.log(level, u'{}'.format(tag1[0].text.strip(' \t\r\n')))
                    else:
                        logging.log(level, u'页面错误')
        except Exception, e:
            if level != None:
                logging.log(level, 'Exp {0} : {1}'.format(FuncName(), e))
            return 0
        else:
            return 1

    def relax_wait(self, target, delay):
        self.set_local_time()
        while 1:
            self.click(logging.INFO)
            diff = self.compare_local_time(target)
            if (diff <= 60) and (diff >= -60):
                break;
            time.sleep(delay)

    def busy_wait(self, target):
        self.set_local_time()
        while 1:
            diff = self.compare_local_time(target)
            if (diff <= 0.5):
                break;

def click_task(jd, target, id):    
    cnt = 0
    logging.warning(u'进程{}:开始运行'.format(id+1))
    while(wait_flag.value != 0):
        pass
    while(run_flag.value != 0):
        cnt = cnt + jd.click(None)
    jd.click(logging.WARNING)
    return cnt

if __name__ == '__main__':
    # help message
    parser = argparse.ArgumentParser(description='Simulate to login Jing Dong, and click coupon')
    parser.add_argument('-k', '--key', 
                        help='Coupon key', required=True)
    parser.add_argument('-r', '--role_id', 
                        help='Coupon role id', required=True)
    parser.add_argument('-hh', '--hour', 
                        type=int, help='Target hour', default=10)
    parser.add_argument('-m', '--minute', 
                        type=int, help='Target minute', default=0)
    parser.add_argument('-p', '--process', 
                        type=int, help='Number of processes', default=1)
    parser.add_argument('-l', '--log', 
                        help='Log file', default=None)

    options = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - (%(levelname)s) %(message)s', datefmt='%H:%M:%S')  
    if (options.log != None):
        log_hdl = logging.FileHandler(options.log,"w")  
        log_hdl.setLevel(logging.WARNING)
        log_fmt = logging.Formatter("%(asctime)s - %(message)s", '%H:%M:%S')  
        log_hdl.setFormatter(log_fmt)  
        logging.getLogger('').addHandler(log_hdl)
    jd = JDCoupon()
    if not jd.pc_login():
        sys.exit(1)
    jd.setup(options.key, options.role_id)
    jd.click(logging.WARNING)
    target = (options.hour * 3600) + (options.minute * 60)
    jd.relax_wait(target, 5)
    jd.click(logging.WARNING)
    wait_flag = multiprocessing.Value('i', 0)
    run_flag = multiprocessing.Value('i', 0)
    pool = multiprocessing.Pool(processes=options.process+1)
    result = []
    h, m, s = jd.format_local_time()
    logging.warning(u'#开始时间 {:0>2}:{:0>2}:{:0>2} #目标时间 {:0>2}:{:0>2}:{:0>2}'.format(h, m, s, options.hour, options.minute, 0))
    wait_flag.value = 1
    run_flag.value = 1
    for i in range(options.process):
        result.append(pool.apply_async(click_task, args=(jd, target, i,)))
    jd.busy_wait(target)
    wait_flag.value = 0
    run_time = jd.duration
    time.sleep(run_time)
    h, m, s = jd.format_local_time()
    logging.warning(u'#结束时间 {:0>2}:{:0>2}:{:0>2} #目标时间 {:0>2}:{:0>2}:{:0>2}'.format(h, m, s, options.hour, options.minute, 0))
    run_flag.value = 0
    pool.close()
    pool.join()
    cnt = 0
    for res in result:
        cnt += res.get()
    logging.warning(u'运行{}秒，点击{}次'.format(run_time, cnt))