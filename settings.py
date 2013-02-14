#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

APP_URL = 'http://app.inside.by/'

HEADERS = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0'}

BSEU_SCHEDULE_URL = 'http://bseu.by/schedule/'

#week
BSEU_WEEK_PERIOD = 2
BSEU_SEMESTER_PERIOD = 3

ACTION_ID = '__id.25.main.inpFldsA.GetSchedule__sp.7.results__fp.4.main'

SCHEDULE_VIEW_ARGS = 'faculty=%s&group=%s&course=%s&form=%s'

LINKS = '<h3>Постоянная ссылка</h3><a href="/link/2/%s">На неделю</a> | <a href="/link/3/%s">На семестр</a>'

COMMENT_NOTIFICATION_SUBJECT = "New comment for Scheduler+"

COMMENT_NOTIFICATION_RECIPIENT = "Stanislau Charniakou <stas.cherniakov@gmail.com>"

API_APP = {
    'APP_NAME': 'scheduler',
    'CONSUMER_KEY': 'app.inside.by',
    'CONSUMER_SECRET': '23xTWhAeLw87YHaOZZh1aNgT',
    'SCOPES': ['https://www.google.com/calendar/feeds/']
}


ROOT_PATH = os.path.dirname(__file__)
TEMPLATE_DIRS = (
    ROOT_PATH + '/templates',
)