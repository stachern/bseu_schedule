#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from datetime import date, datetime, timedelta
from dateutil.relativedelta import *
from dateutil.relativedelta import relativedelta

import leaf

WEEKDAYS = {
    u'понедельник': 1,
    u'вторник': 2,
    u'среда': 3,
    u'четверг': 4,
    u'пятница': 5,
    u'суббота': 6
}

MAIN_TABLE_PATTERN = re.compile(r'<table\b.*?>.*?</table>', re.DOTALL)


def get_semester_start_date():
    current_date = datetime.now().date()
    year_start = date(current_date.year, 1, 1)
    if current_date.month >= 8 or current_date.month == 1:
        # if it's past august - semester would start
        semester_start = year_start + relativedelta(month=9, day=1)
    else:
        # usually it's the first monday of february for the second semester, but we need a day before
        semester_start = year_start + relativedelta(month=2, weekday=MO(0))

    return datetime(semester_start.year, semester_start.month, semester_start.day)


def get_date_offset(current_week, current_day):
    return timedelta(weeks=int(current_week) - 1, days=int(current_day) - 1)


def get_document(raw_html_schedule):
    return leaf.parse(leaf.strip_symbols(leaf.strip_accents(show(raw_html_schedule))))


def get_rows(document):
    return document.get('table')('tr')


def parse_header(header_td):
    current_week = re.findall('\w+(?=\-)', header_td.text)[0]
    current_day = WEEKDAYS[header_td.text.split(u',')[0]]
    return current_week, current_day


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
    document = get_document(raw_html_schedule)
    for tr in get_rows(document):
        schedule_class = {}
        tds = tr.xpath('td')
        if not tds:
            continue
        if len(tds) == 1 and tds[0].colspan == '3':
            # one element and colspan usually means a header
            current_week, current_day = parse_header(tds[0])
        else:
            if not u'подгр.' in tds[0].text and (current_week and current_day):
                schedule_class['subject'] = tds[1].text.rstrip(u' (')

                start_date = semester_start_date + get_date_offset(current_week, current_day)
                time_string = tds[0].text.split(u'-')
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
                        if tr.xpath('td/em'):
                            schedule_class['description'] += u'(%s)' % tr.xpath('td/em')[0].text
                            break

                schedule.append(schedule_class)
            else:
                schedule[len(schedule) - 1]['location'] += u'\n%s%s - %s' % (tds[0].text,
                                                                            (tr.xpath('td/em')[0].text or u'-'),
                                                                             tds[1].text)
    return schedule
