#!/usr/bin/env python
# -*- coding: utf-8 -*-

APP_URL = 'https://bseu-api.appspot.com'

HEADERS = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0'}

BSEU_SCHEDULE_URL = 'http://bseu.by/schedule/'
BSEU_WEEK_PERIOD = 2
BSEU_SEMESTER_PERIOD = 3
BSEU_FACULTY_LIST = [
    ("450", "Аспир."),
    ("18", "ВШУБ"),
    ("432", "ИСГО"),
    ("531", "Консалтторгцентр (в)"),
    ("497", "Консалтторгцентр (о)"),
    ("129", "Магистр."),
    ("12", "УЭФ"),
    ("14", "ФКТИ"),
    ("263", "ФМБК"),
    ("13", "ФМк"),
    ("7", "ФМЭО"),
    ("2", "ФП"),
    ("8", "ФФБД"),
    ("534", "ФЦЭ"),
    ("11", "ФЭМ")
]

ACTION_ID = '__id.25.main.inpFldsA.GetSchedule__sp.7.results__fp.4.main'

SCHEDULE_VIEW_ARGS = 'faculty=%s&group=%s&course=%s&form=%s'

COMMENT_NOTIFICATION_SUBJECT = "New comment for Scheduler+"

COMMENT_NOTIFICATION_RECIPIENT = "Dzianis Dashkevich <dskecse@gmail.com>"

API_APP = {
    'APP_NAME': 'scheduler',
    'CONSUMER_KEY': 'app.inside.by',
    'CONSUMER_SECRET': '23xTWhAeLw87YHaOZZh1aNgT',
    'SCOPES': ['https://www.google.com/calendar/feeds/']
}
