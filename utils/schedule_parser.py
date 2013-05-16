#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from datetime import date, datetime, timedelta
from dateutil.relativedelta import *

import leaf

WEEKDAYS = {u'понедельник': 1, u'вторник': 2, u'среда': 3, u'четверг': 4, u'пятница': 5, u'суббота': 6}
MAIN_TABLE_PATTERN = re.compile(r'<table\b.*?>.*?</table>', re.DOTALL)


def get_semester_start_date():
    current_date = datetime.now().date()
    year_start = date(current_date.year, 1, 1)
    if current_date.month >= 8 or current_date.month == 1:
        #if it's past august - semester would start
        semester_start = year_start + relativedelta(month=9, day=1)
    else:
        #usually it's the first monday of february for the second semester, but we need a day before
        semester_start = year_start + relativedelta(month=2, weekday=SU(0))

    return datetime(semester_start.year, semester_start.month, semester_start.day)


def show(raw_html_schedule):
    """
    cut table with schedule out of the html
    """
    return MAIN_TABLE_PATTERN.findall(raw_html_schedule.decode('cp1251'))[0]


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
            if not u'подгр.' in tds[0].text:
                schedule_class['subject'] = tds[1].text.rstrip(u' (')

                delta = timedelta(weeks=int(current_week) - 1, days=int(current_day))
                start_date = semester_start_date + delta
                time_string = tds[0].text.split(u'-')
                print time_string
                start_time = timedelta(hours=int(time_string[0].split(u':')[0]),
                                       minutes=int(time_string[0].split(u':')[1]))
                end_time = timedelta(hours=int(time_string[1].split(u':')[0]),
                                     minutes=int(time_string[1].split(u':')[1]))
                schedule_class['date'] = {'start': start_date + start_time, 'end': start_date + end_time}
                schedule_class['location'] = tds[2].text
                schedule_class['description'] = tr.get('td span').text

                for ltype in [u'Лекции', u'Семинары', u'Занятия в составе подгруппы']:
                    if ltype in tr.xpath('td/span')[0].text:
                        # check if lecturer is listed
                        if len(tr.xpath('td/em')) > 0:
                            schedule_class['description'] += u'(%s)' % tr.xpath('td/em')[0].text
                            break

                schedule.append(schedule_class)
            else:
                schedule[len(schedule) - 1]['location'] += u'\n%s%s - %s' % (tds[0].text,
                                                                            (tr.xpath('td/em')[0].text or u'-'),
                                                                            tds[1].text)
    return schedule
