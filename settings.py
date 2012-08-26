#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

HEADERS = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0'}

BSEUURL = 'http://bseu.by/schedule/'

ARGS = 'faculty=%s&group=%s&course=%s&form=%s'

LINKS = '<h3>Постоянная ссылка</h3><a href="/scheduleapi?action=view&%s">На неделю</a> | <a href="/scheduleapi?action=view&period=3&%s">На семестр</a>'

subject = "New comment for Scheduler+"

to = "Stanislau Charniakou <stas.cherniakov@gmail.com>"

API_APP = {
    'APP_NAME': 'scheduler',
    'CONSUMER_KEY': 'app.inside.by',
    'CONSUMER_SECRET': '23xTWhAeLw87YHaOZZh1aNgT',
    'SCOPES': ['https://www.google.com/calendar/feeds/']
}

TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__),'templates'),'')