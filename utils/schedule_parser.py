#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

import re
from datetime import date, datetime, timedelta
from dateutil.relativedelta import *

from google.appengine.ext.webapp import template

import leaf
import settings

WEEKDAYS = {u'понедельник': 1, u'вторник': 2, u'среда': 3, u'четверг': 4, u'пятница': 5, u'суббота': 6}
MAIN_TABLE_PATTERN = re.compile(r'<table\b.*?>.*?</table>', re.DOTALL)


def get_semester_start_date():
    current_date = datetime.now().date()
    year_start = date(current_date.year, 1, 1)
    if current_date.month >= 8 or current_date.month == 1:
        #if it's past august - semester would start
        semester_start = year_start + relativedelta(month=9, day=1)
    else:
        #usually it's the first monday of february for the second semester
        semester_start = year_start + relativedelta(month=2, weekday=MO(0))

    return semester_start


def show(raw_html_schedule):
    """
    cut table with schedule out of the html
    """

    try:
        return MAIN_TABLE_PATTERN.findall(raw_html_schedule.decode('cp1251'))[0]
    except IndexError:
        return template.render(os.path.join(settings.ROOT_PATH, 'templates/html/misc/no_schedule_alert.html'), {})


def read(raw_html_schedule):
    """
    parses html an return a well formed list of dicts
    """
    semester_start_date = get_semester_start_date()
    schedule = []
    check = False
    document = leaf.parse(leaf.strip_symbols(leaf.strip_accents(show(raw_html_schedule))))
    table = document.get('table')
    trs = table('tr')
    for tr in trs:
        schedule_class = {}
        tds = tr.xpath('td')
        for td in tds:
            if td.colspan == '3':
                current_week = re.findall('\w+(?=\-)', td.text)[0]
                current_day = WEEKDAYS[td.text.split(u',')[0]]
                check = False
            else:
                check = True

        if check:
            if not u'подгр' in tds[0].text:
                schedule_class['subject'] = tds[1].text.rstrip(u' (')

                delta = timedelta(weeks=int(current_week) - 1, days=int(current_day))
                start_date = semester_start_date + delta
                time_string = tds[0].text.split(u'-')
                start_time = timedelta(hours=int(time_string[0].split(u':')[0]),
                                       minutes=int(time_string[0].split(u':')[1]))
                end_time = timedelta(hours=int(time_string[1].split(u':')[0]),
                                     minutes=int(time_string[1].split(u':')[1]))
                schedule_class['date'] = {'start': start_date + start_time, 'end': start_date + end_time}
                schedule_class['location'] = tds[2].text
                schedule_class['description'] = tr.get('td span').text

                if u'Лекции' in tr.xpath('td/span')[0].text \
                or u'Семинары' in tr.xpath('td/span')[0].text:
                    schedule_class['description'] += u'(%s)' % tr.xpath('td/em')[0].text

                schedule.append(schedule_class)
            else:
                schedule[len(schedule) - 1]['location'] += u'\n%s%s - %s' % (tds[0].text,
                                                                            (tr.xpath('td/em')[0].text or u'-'),
                                                                            tds[1].text)
    return schedule
