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
    global curweek
    startsem = datetime.strptime('2012-02-05', '%Y-%m-%d')
    weekdaysD = {u'понедельник': 1, u'вторник': 2, u'среда': 3, u'четверг': 4, u'пятница': 5, u'суббота': 6}
    sched = []
    check = False

    document = leaf.parse(leaf.strip_symbols(leaf.strip_accents(htmltext.decode('cp1251'))))
    table = document.get('table')
    trs = table('tr')
    for tr in trs:
        classd = {}
        tds = tr.xpath('td')
        for td in tds:
            if td.colspan == '3':
                curweek = re.findall('\w+(?=\-)', td.text)[0]
                curday = weekdaysD[td.text.split(u',')[0].encode('latin1').decode('utf-8')]
                check = False
            else:
                check = True

        if check:
            if not u'подгр' in tds[0].text.encode('latin1').decode('utf-8', 'ignore'):
                classd['subject'] = tds[1].text.rstrip(u' (').encode('latin1').decode('utf-8', 'ignore')

                delta = timedelta(weeks=int(curweek) - 1, days=int(curday))
                startdate = startsem + delta
                timesch = tds[0].text.split(u'-')
                stime = timedelta(hours=int(timesch[0].split(u':')[0]), minutes=int(timesch[0].split(u':')[1]))
                etime = timedelta(hours=int(timesch[1].split(u':')[0]), minutes=int(timesch[1].split(u':')[1]))
                classd['date'] = {'start': startdate + stime, 'end': startdate + etime}
                classd['location'] = tds[2].text.encode('latin1').decode('utf-8', 'ignore')
                classd['description'] = tr.get('td span').text.encode('latin1').decode('utf-8', 'ignore')

                if u'Лекции' in tr.xpath('td/span')[0].text.encode('latin1').decode('utf-8', 'ignore') \
                or u'Семинары' in tr.xpath('td/span')[0].text.encode('latin1').decode('utf-8','ignore'):
                    classd['description'] += u'(%s)' % tr.xpath('td/em')[0].text.encode('latin1').decode('utf-8','ignore')

                sched.append(classd)
            else:
                sched[len(sched) - 1]['location'] += u'\n%s%s - %s' % (
                tds[0].text.encode('latin1').decode('utf-8', 'ignore'),
                (tr.xpath('td/em')[0].text or u'-').encode('latin1').decode('utf-8', 'ignore'),
                tds[1].text.encode('latin1').decode('utf-8', 'ignore'))

    return sched
