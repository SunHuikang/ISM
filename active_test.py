# -*- coding: utf-8 -*-
import json
import requests
import re
import sys
from haralyzer import HarParser, HarPage
from browsermobproxy import Server

server = Server("E:/Test_Code/Pro_py2/browsermob-proxy-2.1.4/bin/browsermob-proxy")
server.start()
proxy = server.create_proxy()

def getip():
    r = requests.get('http://2017.ip138.com/ic.asp')
    ip = r.text.split('[')[1].split(']')[0]
    return ip

def GetOnloadtime(url, site, initial_url):
    from selenium import webdriver

    service_args = [
        '--proxy=%s' % proxy.proxy,
        '--proxy-type=http',
        '--disk-cache=no',
        '--ignore-ssl-errors=true'
    ]

    driver = webdriver.PhantomJS(service_args=service_args)

    proxy.new_har("test")
    website_url = 'http://' + url
    driver.get(website_url)
    # driver.get("http://www.baidu.com")

    har = json.dumps(proxy.har, indent=4)
    filename = url + '.har'
    outfile = open(filename, 'w')
    # outfile = open("www.baidu.com.har", 'w')
    print(har, file=outfile)

    data = driver.execute_script("return window.performance.timing")
    # =json.dumps(data)
    loadEventEnd = data.get("loadEventEnd")
    start = data.get("navigationStart")
    loadTime = loadEventEnd - start
    # print("页面onload时间:", loadTime)

    server.stop()
    driver.quit()
    # print(loadTime)
    srcip = getip()
    data = {"time": loadTime/1000, "method": 'A', "site": site, "srcip": srcip}
    data_json=json.dumps(data)
    print(data_json)
    print(type(data_json))
    # 测试阶段先不回传数据
    # headers = {'content-type': 'application/json'}
    # post_url = initial_url + 'meassitetimeraw/'
    # requests.post(post_url, data_json, headers=headers)


def GetResources(url, site, initial_url):
    filename = url + '.har'
    with open(filename, 'r', encoding='UTF-8') as f_1:
        temp = json.loads(f_1.read())
        # 转换成dict类型
        page_id = temp['log']['pages'][0]['id']
        # 获取page_id
        har_page = HarPage(page_id, har_data=temp)

    filename = url + '.json'
    f_2 = open(filename, 'w')
    list = []
    for i in range(len(har_page.entries)):
        num = i + 1
        url = har_page.entries[i]['request']['url']
        domain_list = re.findall(r"//(.+?)/", url)
        ip = har_page.entries[i]['serverIPAddress']
        mimeType = har_page.entries[i]['response']['content']['mimeType']
        # size_kb = har_page.entries[i]['response']['content']['size'] / 1024
        # size = round(size_kb, 1)  # 保留小数点后1位
        size_b = har_page.entries[i]['response']['bodySize']
        size_kb = har_page.entries[i]['response']['bodySize'] / 1024
        size_kb = round(size_kb, 1)  # 保留小数点后1位
        data = {'num': num, 'url': url, 'ip': ip, 'mimeType': mimeType, 'size': size_b, 'domain':domain_list[0]}
        list.append(data)
    resources = json.dumps(list, indent=4)
    print(resources, file=f_2)
    #print(resources)
    f_2.close

    # 得到总共有几个域名
    domain_list = []
    for item in json.loads(resources):
        # print(item)
        domain = item['domain']

        if domain in domain_list:
            continue
        else:
            domain_list.append(domain)
    # print(domain_list)

    for host in domain_list:
        size = 0
        for item in json.loads(resources):
            domain = item['domain']
            if domain == host:
                ip = item['ip']
                size = size + item['size']
            else:
                continue
        expired = "2086-03-09T21:00:00+08:00"
        data = {"site": site, 'domain': host, 'ip': ip, 'expired': expired , 'size':size}
        data_json = json.dumps(data)
        print(data_json)


def main(initial_url):
    get_url = initial_url + 'site/'
    result = requests.get(get_url)
    # print(result.text)
    # print(type(result.text)) #str
    result_list = json.loads(result.text)
    print(result_list)
    # print(type(result_list)) #list
    url_list = []

    for i in range(len(result_list)):
        # print(result_list[i])
        # print(type(result_list[i])) #dict
        url = result_list[i]['url']
        site = i + 1
        url = url[8:]
        # print(url)
        # print(site)
        GetOnloadtime(url, site, initial_url)

    for i in range(len(result_list)):
        url = result_list[i]['url']
        site = i + 1
        url = url[8:]
        GetResources(url, site, initial_url)
    # GetResources('www.360.cn','2')


if __name__ == '__main__':
    url = sys.argv[1]
    main(url)