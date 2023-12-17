#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from datetime import datetime, timedelta

import leaf


MAIN_TABLE_PATTERN = re.compile(r'<table\b.*?>.*?</table>', re.DOTALL)


def get_document(raw_html_schedule):
    return leaf.parse(leaf.strip_symbols(leaf.strip_accents(show(raw_html_schedule))))


def get_rows(document):
    return document.get('table')('tr')


def parse_header(header_td):
    # header_td: u'пятница (29.9.2023)'
    current_date = re.findall('\((.+)\)', header_td.text)[0] # u'29.9.2023'
    return datetime.strptime(current_date, '%d.%m.%Y')


def show(raw_html_schedule):
    """
    cut table with schedule out of the html
    """
    return MAIN_TABLE_PATTERN.findall(raw_html_schedule.decode('cp1251'))[0]


def read(raw_html_schedule):
    """
    parses html and returns a well-formed list of dicts
    """
    schedule = []
    document = get_document(raw_html_schedule)
    for tr in get_rows(document):
        schedule_class = {}

        # Uncomment to debug
        # print(tr.html())

        # 1: <tr><td><caption>Расписание на неделю для группы 20 ДАИ-1, 4 курса</caption></td></tr>

        # 2: <tr><th width="96px">Время</th><th colspan="2">Дисциплина, преподаватель</th><th width="40px">к./ауд.</th></tr>

        # 3: <tr><td colspan="5" class="wday">суббота (23.9.2023)</td></tr>

        # 4: <tr><td class="right">13:05-14:25</td><td colspan="2">Международный бизнес <span class="distype">(Лекции)</span> ,  <span class="teacher">Есаян Олег Есаевич</span></td><td class="right">3/250</td></tr>
        # 16:05-17:25	Международная инвестиционная деятельность (Лекции) , Петрушкевич Елена Николаевна	3/332

        # 5: <tr><td rowspan="8">17:45-19:05</td><td colspan="3">Иностранный язык (1-й) <span class="distype">(Практические занятия)</span></td></tr>
        # 17:45-19:05	Иностранный язык (1-й) (Практические занятия)

        # 6: <tr><td class="sg" rowspan="1">подгр.ан.1</td><td><span class="teacher">Карлова Галина Григорьевна</span></td><td rowspan="1">1/408<!--7, igrp 7, week[i]: 5, week[igrp] 5--></td></tr>

        tds = tr.xpath('td')
        if not tds or not tds[0].text: # [2] or [1]
            continue

        if len(tds) == 1 and tds[0].colspan == '5': # [3]
            # one element and colspan usually means a header
            current_date = parse_header(tds[0])
        else:

            if not u'подгр.' in tds[0].text and current_date: # [4] or [5]
                schedule_class['subject'] = tds[1].text.rstrip(u' (') # u'Международная инвестиционная деятельность' or u'Иностранный язык (1-й)'

                class_start, class_end = tds[0].text.split(u'-') # u'16:05-17:25' => [u'16:05', u'17:25']
                start_time_seconds = timedelta(hours=int(class_start.split(u':')[0]), minutes=int(class_start.split(u':')[1]))
                end_time_seconds = timedelta(hours=int(class_end.split(u':')[0]), minutes=int(class_end.split(u':')[1]))

                schedule_class['date'] = {'start': current_date + start_time_seconds, 'end': current_date + end_time_seconds}
                schedule_class['location'] = tds[2].text if len(tds) > 2 else u''  # u'3/332' or u'' (subgroups will be added in an "else" below)

                # u'<span class="distype">(Лекции)</span>' or u'<span class="distype">(<strong>Зачет</strong>)</span>'
                span = tr.get('td span.distype')
                if span.get('strong'):
                    schedule_class['description'] = span.get('strong').text # u'Зачет' or u'Экзамен'
                else:
                    schedule_class['description'] = re.findall('\((.+)\)', span.text)[0] # u'Лекции' or u'Практические занятия'

                # check to see if a lecturer is listed
                if tr.get('td span.teacher'):
                    schedule_class['description'] += u' (%s)' % tr.get('td span.teacher').text

                schedule.append(schedule_class)

            else: # [6]
                # adds proper subgroup info
                schedule[len(schedule) - 1]['location'] += u'\n%s %s - %s' % (tds[0].text, # u'подгр.ан.1'
                                                                            (tr.get('td span.teacher').text or u'-'), # u'Карлова Галина Григорьевна'
                                                                             tds[2].text) # '1/408'

    # Uncomment to debug
    # for ev in list(schedule):
    #     for k, v in ev.iteritems():
    #         if k is "date":
    #             print('{0}: {1}'.format(k, repr(v)))
    #         else:
    #             print('{0}: {1}'.format(k, v.encode('utf-8')))
    #     print("****")
    # raise Exception

    return schedule
