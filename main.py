#coding:UTF-8

#libraries needs to be installed
#selenium, pyyaml, slackclient, bs4, lxml
# and phantomjs

# get ChromeDriver from here
# https://sites.google.com/a/chromium.org/chromedriver/downloads

from __future__ import absolute_import, division, print_function

import sys
import json
import re

import datetime
import time

import urllib

from selenium import webdriver
from selenium.webdriver.support.events import EventFiringWebDriver
from selenium.webdriver.support.events import AbstractEventListener

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.select import Select

from bs4 import BeautifulSoup
import json
import yaml
import os
from slackclient import SlackClient
from time import sleep

#FOR REAL USE set this to be True to hide Chrome screen
HEADLESSNESS = True

#defalut value
SLACK_TOKEN = ''
SLACK_NOTIFIER_USERS = ''
SEARCH_STRING = ''

#loading credentials
args = sys.argv
# credentials_mukai.yaml
with open(args[1], "r", encoding="utf-8_sig") as stream:
    try:
        credentials = yaml.load(stream, Loader=yaml.SafeLoader)
        globals().update(credentials)
    except yaml.YAMLError as exc:
        print(exc)

FORMAT = "%Y-%m-%d %H:%M:%S"

#for notifieruser in SLACK_NOTIFIER_USER:
if SLACK_NOTIFIER_USERS == "ALL":
    sc = SlackClient(SLACK_TOKEN)
    _slack_users_list = sc.api_call(
    "users.list"
    )
    filtered_members = list(filter(lambda x: (x.get('deleted') == False) and (x.get('is_bot') == False),_slack_users_list.get('members')))
    slack_users_list = []
    for members in filtered_members:
        _id = members[u'id']
        #print(members[u'name'],members[u'deleted'],members[u'is_restricted'],members[u'is_ultra_restricted'],members[u'is_bot'])
        if _id != "USLACKBOT":
            slack_users_list.append(_id)
else:
    slack_users_list = SLACK_NOTIFIER_USERS

def delete_reminder(reminder_id):
    sc = SlackClient(SLACK_TOKEN)
    return sc.api_call(
        "reminders.delete",
        token=SLACK_TOKEN,
        reminder=reminder_id
    )

def post_reminder(text,time,user):
    sc = SlackClient(SLACK_TOKEN)
    return sc.api_call(
        "reminders.add",
        text=text,
        time=int(time),
        user=user
    )

# get "HH:MM - HH:MM" string and return a tuple that contains two time objects
def parse_start_end(start_end):

    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d ")
    start, end = start_end.split(" - ")
    start_time = datetime.datetime.strptime(date_str + start, "%Y-%m-%d " + "%H:%M")
    end_time = datetime.datetime.strptime(date_str + end, "%Y-%m-%d " + "%H:%M")

    return (start_time,end_time)

class ScreenshotListener(AbstractEventListener):
    #count for error screenshots
    exception_screenshot_count = 0

    def on_exception(self, exception, driver):
        screenshot_name = "00_exception_{:0>2}.png".format(ScreenshotListener.exception_screenshot_count)
        ScreenshotListener.exception_screenshot_count += 1
        driver.get_screenshot_as_file(screenshot_name)
        print("Screenshot saved as '%s'" % screenshot_name)

def makeDriver(*, headless=True):
    options = Options()
    if(headless):
        options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1280,800')
    _driver = webdriver.Chrome(options=options)
    return EventFiringWebDriver(_driver, ScreenshotListener())

def toRemindSchDate(sch_ymd):
    if len(sch_ymd) == 5:
      sch_ymd = str(datetime.date.today().year) + "/"  + sch_ymd

    sch_ymd = sch_ymd + " " + "18:00:00"

    return datetime.datetime.strptime(sch_ymd, '%Y/%m/%d %H:%M:%S')

def loginDesknets(driver):
    url = DN_URL

    driver.get(url)
    driver.implicitly_wait(10)

    userId_box = driver.find_element_by_name('UserID')
    pass_box = driver.find_element_by_name('_word')
    userId_box.send_keys(DN_USERNAME)
    pass_box.send_keys(DN_PASSWORD)

    #driver.save_screenshot('0before login.png')
    #print( "saved before login" )

    #login
    driver.find_element_by_id('login-btn').click()

    #elemは特に使わないが、ページが表示されるまで待ちたいため入れている
    elem = driver.find_element_by_css_selector(".portal-cal-body")

    print("URL:" + driver.current_url)

    return driver

#スケジュールを取得して[{start:時間, title:タイトル, location:場所}, ...] の形式で返す
def getSchedule(driver):

    #スケジュールを選択
    elem = driver.find_element_by_css_selector("#dn-h-search > form > input.searchbox")
    elem.send_keys(SEARCH_STRING)

    #driver.save_screenshot('0after login.png')

    element = driver.find_element_by_xpath("//*[@id='dn-h-search']/form/select")
    Select(element).select_by_value("sch")

    #driver.save_screenshot('1after login.png')

    elem = driver.find_element_by_css_selector("#dn-h-search > form > input.jdn-h-search-button")
    elem.click()

    #driver.save_screenshot('2after login.png')

    trs = driver.find_element_by_xpath("//*[@id='searchfrm']/table/tbody").find_elements(By.TAG_NAME, "tr")

    driver.implicitly_wait(2)
    calendar_items = []

    for i in range(0,len(trs)):
       tds = trs[i].find_elements(By.TAG_NAME, "td")
       for j in range(1,len(tds)):
           if j < len(tds):
               #日付
               if j == 1:
                  sch_ymd = toRemindSchDate(tds[j].text)
               #開始時間
               elif j == 2:
                  start_time = tds[j].text
               #終了時間
               elif j == 3:
                  end_time = tds[j].text
               #タイトル
               elif j == 4:
                   title = tds[j].text
               #場所
               elif j == 5:
                  location = tds[j].text

       #print("title:%s, sch_ymd:%s, start_time:%s, end_time:%s, location:%s" % (title,sch_ymd,start_time,end_time,location))
       calendar_items.append( (title,sch_ymd,start_time,end_time,location) )

    return calendar_items

################## main starts here ##################################
if __name__ == "__main__":
    print( "【start】" + str(datetime.datetime.now()))

    sc = SlackClient(SLACK_TOKEN)

    driver = makeDriver(headless=HEADLESSNESS)
    print( 'driver created' )

    try:

        loginDesknets(driver)

        schedule_items = getSchedule(driver)

    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise
    finally:
        if HEADLESSNESS:
            driver.quit()

    current_reminders = sc.api_call(
    "reminders.list"
    )
    if not current_reminders.get('ok'):
        print('Slack接続エラー:' +current_reminders.get('error'))

    filtered_reminders = list(filter((lambda x: (x.get('complete_ts') == 0) and x.get('recurring') == False),current_reminders.get('reminders')))

    #make {time:{title:[id, ...]}} dictionary of current reminders
    text_id_dic = {}
    user_id_dic = {}
    for reminder in filtered_reminders:
        _id = reminder[u'id']
        _time = reminder[u'time']
        _text = reminder[u'text']
        _user = reminder[u'user']

        #print("text_id_dic:"+str(text_id_dic))
        if _time not in text_id_dic:
            text_id_dic[_time] = {}

        if _text not in text_id_dic[_time]:
            text_id_dic[_time][_text] = []

        if _time not in user_id_dic:
            user_id_dic[_time] = {}

        if _user not in user_id_dic[_time]:
            user_id_dic[_time][_user] = []

        text_id_dic[_time][_text].append(_id)
        user_id_dic[_time][_user].append(_id)

    cnt_false = 0
    cnt_True = 0
    cnt_None = 0
    for schedule_item in schedule_items:
        #start_time, sch_ymd, end_time, title = schedule_item
        title, sch_ymd, start_time, end_time, location = schedule_item

        #print("title:%s, sch_ymd:%s, start_time:%s, end_time:%s, location:%s" % (title,sch_ymd,start_time,end_time,location) )
        message = "%s %s-%s @%s" % (title, start_time, end_time, location)
        unix_starttime = int(time.mktime( sch_ymd.timetuple() ))

        for slack_user in slack_users_list:
            if((unix_starttime in text_id_dic) and (message in text_id_dic[unix_starttime]) and (unix_starttime in user_id_dic) and (slack_user in user_id_dic[unix_starttime])  ):
                cnt_None+=1
            elif time.time() <= unix_starttime :
                #print("posting reminder message:", message, " time:", datetime.datetime.utcfromtimestamp(unix_starttime), " user:", slack_user)
                response = post_reminder(message,unix_starttime,slack_user)
                #print(response)
                _ok = response[u'ok']
                if _ok == True:
                    cnt_True+=1
                elif _ok == False:
                    #print(str(datetime.datetime.now())," posting reminder message:", message, " time:", datetime.datetime.utcfromtimestamp(unix_starttime), " user:", slack_user)
                    cnt_false+=1
                # slackの通信制限に引っかかる可能性があるため待機をいれる
                sleep(3)

    print( "【end  】" + str(datetime.datetime.now()) + " True:" + str(cnt_True) + " False:" + str(cnt_false) + " None:" + str(cnt_None))
