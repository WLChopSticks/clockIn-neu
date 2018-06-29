import requests
from lxml import etree
import re
import urllib
from urllib import parse
import pytesseract
from PIL import Image, ImageEnhance
import datetime
import time

users = {

}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36"
}

username = ''
password = ''
cookie = ''
retry_count = 5
notice_string = ''


def getCaptcha():
    # 获取验证码图片
    image_url = 'http://kq.neusoft.com/imageRandeCode'
    headers['Cookie'] = cookie

    response = requests.get(image_url, headers=headers)
    with open('captchar.jpg', 'wb') as f:
        f.write(response.content)

    im = Image.open('captchar.jpg')
    enhancer = ImageEnhance.Color(im)
    enhancer = enhancer.enhance(0)
    enhancer = ImageEnhance.Brightness(enhancer)
    enhancer = enhancer.enhance(2)
    enhancer = ImageEnhance.Contrast(enhancer)
    enhancer = enhancer.enhance(8)
    enhancer = ImageEnhance.Sharpness(enhancer)
    im = enhancer.enhance(20)
    with open('newcaptchar.jpg', 'wb') as f:
        f.write(response.content)

    #识别验证码
    captcha = pytesseract.image_to_string(im, config="-psm 8 -c tessedit_char_whitelist=1234567890")
    print(captcha)
    return captcha

def prepareParamters(username, password):

    time.sleep(2)
    login_page_url = 'http://kq.neusoft.com/index.jsp'
    response = requests.get(url=login_page_url, headers = headers)

    html = etree.HTML(response.text)
    with open(r'source.txt','w') as f_tem:
        f_tem.write(response.text)

    textfield_name_list = html.xpath('//input[@class="textfield"]/@name')

    #获取用户名密码的html 名称
    username_key = textfield_name_list[0]
    password_key = textfield_name_list[1]

    #获取验证码的html 名称
    captcha_name_list = html.xpath('//input[@class="a"]/@name')
    captcha_key = captcha_name_list[0]

    #获取neusoft_key
    neusoft_key_field = html.xpath('//input[@name="neusoft_key"]')[0]
    neusoft_key = neusoft_key_field.attrib['value']

    #获取KEY1530066964607
    key_list = html.xpath('//input[contains(@name,"KEY")]')[0]
    key = key_list.attrib['name']

    #获取cookie
    global cookie
    cookie = username_key.replace('ID',"")
    pattern = re.compile('(.+)!')
    cookie = 'JSESSIONID=' + pattern.findall(cookie)[0]

    #获取验证码
    captcha = getCaptcha()

    # aptcha = input("请输入验证码")

    login_header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36",
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Origin': 'http://kq.neusoft.com',
        'Refer': 'http://kq.neusoft.com/index.jsp',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Connection': 'keep-alive',
        'Cookie': cookie}

    data = {'login' : 'true',
            'neusoft_attendance_online' : '',
            'neusoft_key' : neusoft_key,
            key : '',
            username_key : username,
            password_key : password,
            captcha_key : captcha}
    form_data = urllib.parse.urlencode(data)

    login(data, login_header)
    # print(form_data)



def login(data, login_header):
    print('开始登陆流程')
    login_url = 'http://kq.neusoft.com/login.jsp?'
    response = requests.post(login_url, data=data, headers=login_header, allow_redirects=False)
    #返回code302 进行跳转
    attendance_url = 'http://kq.neusoft.com/attendance.jsp'
    headers['Cookie'] = cookie
    if response.text.find('http://kq.neusoft.com/attendance.jsp') != -1:
        response = requests.get('http://kq.neusoft.com/attendance.jsp', headers=headers)
    else:
        # 如果登录失败, 则需要重新进行逻辑
        if retry_count > 0:
            global retry_count
            retry_count -= 1
            prepareParamters(username, password)
        return

    html = etree.HTML(response.text)

    currentempoid = html.xpath('//input[@name="currentempoid"]/@value')

    #打卡流程
    record_url = 'http://kq.neusoft.com/record.jsp'
    data = {'currentempoid' : currentempoid}
    response = requests.post(record_url, headers = headers, data=data, allow_redirects=False)
    if response.text.find('http://kq.neusoft.com/attendance.jsp') != -1:
        response = requests.get('http://kq.neusoft.com/attendance.jsp', headers=headers)

    #检测打卡是否成功
    checkSuccess(response)


def checkSuccess(response):
    #检测打卡是否成功
    html = etree.HTML(response.text)
    result = html.xpath('//table[@class="kq-message-table"]/tbody//td')
    last_record_time = result[-1].text
    currenttime = datetime.datetime.now().strftime('%H:%M:%S')
    last_record_time = last_record_time.replace(':', '')
    currenttime = currenttime.replace(':', '')

    print(currenttime)
    print(last_record_time)
    global notice_string
    if int(currenttime) - int(last_record_time) < 30 and int(currenttime) - int(last_record_time) >= 0:
        print(username + ' 打卡成功')
        notice_string = notice_string + username + '打卡成功\n'
    else:
        print(username + ' 打卡失败')
        notice_string = notice_string + username + '打卡失败\n'

def start():
    for key, value in users.items():
        global username
        username = key
        global password
        password = value
        print(username)
        print(password)
        prepareParamters(username, password)

def sendNotification():
    sec_key = '2744-e874d4130b17169d7cbd4b0b986f40a0'
    notice_url = 'https://pushbear.ftqq.com/sub?sendkey=' + sec_key + '&text=clock_in_result&desp=' + notice_string
    requests.get(notice_url)


if __name__ == "__main__":

    day_record = False
    night_record = False
    while True:
        print(night_record)
        current_time = int(datetime.datetime.now().strftime('%H%M%S'))
        print(str(current_time))
        if not day_record and current_time - 81000 > 0 and 81330 - current_time > 0:
            print('早上打卡开始')
            start()
            sendNotification()
            day_record = True
        elif not night_record and current_time - 173100 > 0 and 173430 - current_time > 0:
            print('晚上打卡开始')
            start()
            sendNotification()
            night_record = True

        else:
            print('loading...')
            day_record = False
            night_record = False
            global retry_count
            retry_count = 5
            global notice_string
            notice_string = ''

        #延时
        for i in range(1,18):
            print('loading...')
            time.sleep(10)
        time.sleep(6)

    print('打卡完毕')




