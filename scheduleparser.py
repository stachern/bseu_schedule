#!/usr/bin/env python
# -*- coding: utf-8 -*-
#


import re
import leaf
from datetime import datetime, timedelta
import logging

logging.getLogger().setLevel(logging.DEBUG)

def show(htmltext):
    """
    cut table with schedule out of the html
    """
    patt=re.compile(r'<table\b.*?>.*?</table>', re.DOTALL)
    try:
        return patt.findall(htmltext.decode('cp1251'))[0]
    except IndexError:
        return '<h1><center>Нет доступного расписания</center></h1>'

def read(htmltext):
    """
    parses html an return a well formed list of dicts
    """
    startsem = datetime.strptime('2012-08-26','%Y-%m-%d')
    weekdaysD = {u'понедельник': 1, u'вторник': 2, u'среда': 3, u'четверг': 4, u'пятница': 5, u'суббота': 6}
    sched = []
    check = False
    document = leaf.parse(leaf.strip_symbols(leaf.strip_accents(show(htmltext))))
    table = document.get('table')
    trs = table('tr')
    for tr in trs:
        classd = {}
        tds = tr.xpath('td')
        for td in tds:
            if td.colspan == '3':
                curweek = re.findall('\w+(?=\-)', td.text)[0]
                curday = weekdaysD[td.text.split(u',')[0]]
                check = False
            else:
                check = True

        if check:
            if not u'подгр' in tds[0].text:
                classd['subject'] = tds[1].text.rstrip(u' (')

                delta = timedelta(weeks=int(curweek) - 1, days=int(curday))
                startdate = startsem + delta
                timesch = tds[0].text.split(u'-')
                stime = timedelta(hours=int(timesch[0].split(u':')[0]), minutes=int(timesch[0].split(u':')[1]))
                etime = timedelta(hours=int(timesch[1].split(u':')[0]), minutes=int(timesch[1].split(u':')[1]))
                classd['date'] = {'start': startdate + stime, 'end': startdate + etime}
                classd['location'] = tds[2].text
                classd['description'] = tr.get('td span').text

                if u'Лекции' in tr.xpath('td/span')[0].text \
                or u'Семинары' in tr.xpath('td/span')[0].text:
                    classd['description'] += u'(%s)' % tr.xpath('td/em')[0].text

                sched.append(classd)
            else:
                sched[len(sched) - 1]['location'] += u'\n%s%s - %s' % (
                tds[0].text,
                (tr.xpath('td/em')[0].text or u'-'),
                tds[1].text)
    return sched
