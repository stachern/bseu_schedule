#!/usr/bin/env python
# -*- coding: utf-8 -*-

APP_URL = 'https://bseu-api.appspot.com'

HEADERS = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0'}

BSEU_SCHEDULE_URL = 'https://bseu.by/schedule/'
BSEU_WEEK_PERIOD = 2
BSEU_SEMESTER_PERIOD = 3
BSEU_FACULTY_LIST = [
    ("450", u"Аспир."),
    ("18", u"ВШУБ"),
    ("531", u"ИПК и ПЭК (в)"),
    ("497", u"ИПК и ПЭК (о)"),
    ("129", u"Магистр."),
    ("432", u"СЭФ"),
    ("12", u"УЭФ"),
    ("14", u"ФКТИ"),
    ("263", u"ФМБК"),
    ("13", u"ФМк"),
    ("7", u"ФМЭО"),
    ("2", u"ФП"),
    ("8", u"ФФБД"),
    ("534", u"ФЦЭ"),
    ("11", u"ФЭМ")
]

ACTION_ID = '__id.25.main.inpFldsA.GetSchedule__sp.7.results__fp.4.main'

SCHEDULE_VIEW_ARGS = 'faculty=%s&group=%s&course=%s&form=%s'

COMMENT_NOTIFICATION_SUBJECT = "New comment for Scheduler+"

COMMENT_NOTIFICATION_RECIPIENT = "Dennis Dashkevich <dskecse@gmail.com>"

# https://developers.google.com/identity/protocols/oauth2/web-server#python
OAUTH2_SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events'
]

OAUTH2_CONFIG = {
    'project_id': 'bseu-api',
    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
    'token_uri': 'https://oauth2.googleapis.com/token',
    'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
    'redirect_uris': ['http://localhost:8080/calendar_auth', 'https://bseu-api.appspot.com/calendar_auth'],
    'javascript_origins': ['https://bseu-api.appspot.com','http://localhost:8080']
}
