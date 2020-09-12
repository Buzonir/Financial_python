# -*- coding: utf-8 -*-
"""
Created on Fri Sep 11 16:11:30 2020

@author: Buzoni

We wanna get the curve yield from B3 website and interpolate it.
B3 releases the curve in consecutive days.
So the code returs the curve in working days.
"""
from datetime import datetime, timedelta
from urllib.request import urlopen
from bs4 import BeautifulSoup as bs
from bizdays import Calendar
HOLIDAYS_DIC = 'C:/Users/buzon/Documents/Python/Arquivos base/Anbima.txt'

ANBIMA_HOL = open(HOLIDAYS_DIC, 'r')
HOLIDAYS = []
for row in ANBIMA_HOL:
    HOLIDAYS.append(row.strip())
ANBIMA_HOL.close()
cal = Calendar(HOLIDAYS, ['Sunday', 'Saturday'])

FORMAT = '%Y%m%d'

def get_curve_b3(curve_date, index):
    """Get the future di curve from B3. Format YYYYMMDD"""
    date_1 = (curve_date[-2:] + "/" +
              curve_date[4:6] + "/" +
              curve_date[:4])

    url = 'http://www2.bmf.com.br/pages/portal/bmfbovespa\
/lumis/lum-taxas-referenciais-bmf-ptBR.asp?Data={}&\
Data1={}&slcTaxa={}'.format(date_1, curve_date, index.upper())

    page = urlopen(url)
    soup = bs(page, 'html.parser')
    table = soup.find_all('td')

    curve = []
    for i, value in enumerate(table):
        if i % 3 == 0 or i == 0:
            curve.append([int(value.text),
                          float(table[i+1].text.replace(",", "."))])
    #Here, we convert the consecutive days to working days.
    date_stlm = datetime.strptime(curve_date, FORMAT)
    for i, value in enumerate(curve):
        date_fwd = date_stlm + timedelta(value[0])
        value[0] = cal.bizdays(date_stlm, date_fwd)
        
    return curve

def get_dic_curve(date_curve, index):
    """Make a dictionary from a lista"""
    curve = get_curve_b3(date_curve, index)
    dic_curve = {}
    for value in curve:
        dic_curve[value[0]] = value[1]
        
    return dic_curve

def interpolate(wrk_days, given_curve, given_dic):
    """Get the yield given a working date and a given curve.
    If necessary, we make the exponential interpolation of the curve"""
    try:
        yld = given_dic[wrk_days]
    except:
        for vertice in range(1, len(given_curve) + 1):
            if given_curve[vertice][0] > wrk_days:
                wrkds_1 = given_curve[vertice - 1][0]
                yield_1 = given_curve[vertice - 1][1]
                wrkds_2 = given_curve[vertice][0]
                yield_2 = given_curve[vertice][1]
                break
        step_1 = (1 + yield_1)**(wrkds_1/252)
        step_2 = ((1 + yield_2)**(wrkds_2/252))/((1 + yield_1)**(wrkds_1/252))
        step_3 = (wrk_days - wrkds_1)/(wrkds_2 - wrkds_1)
        yld = ((step_1 * (step_2 ** step_3))**(252/wrk_days)) - 1
        
    return yld
