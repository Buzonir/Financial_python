# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 17:41:04 2020

@author: buzon
"""

import matplotlib.pyplot as graph
import B3curve as b3
from datetime import datetime
from bizdays import Calendar
import di_derivative as di

FERIADOS = open('C:/Users/buzon/Documents/Python/Arquivos base/Anbima.txt', 'r')
HOLIDAYS = []
for linha in FERIADOS:
    HOLIDAYS.append(linha.strip())
FERIADOS.close()
cal = Calendar(HOLIDAYS, ['Sunday', 'Saturday'])

INDEX = 'pre'
FORMAT = '%d%m%Y'
FORMAT_B3 = '%Y%m%d'

def historic(start, end, maturity_str):
    """Get the historic yield of a vertice. Format ddmmyyyy"""

    start_dt = datetime.strptime(start, FORMAT)
    end_dt = datetime.strptime(end, FORMAT)
    
    curves_dics = []
    curves_lists = []
    dates_str = []
    dates = []
    next_day = 1
    
    while start_dt <= end_dt:
        start_str = datetime.strftime(start_dt, FORMAT_B3)
        curve_list = b3.get_curve_b3(start_str, INDEX)
        curve_dic = b3.get_dic_curve(curve_list)
        dates.append(start_dt)
        dates_str.append(start_str)
        curves_dics.append(curve_dic)
        curves_lists.append(curve_dic)
        start_dt = cal.offset(start_dt, next_day)
        start_dt = datetime(start_dt.year, start_dt.month, start_dt.day)
    
    maturity = di.get_maturity(maturity_str)
    dates_index = 0
    historic = []
    
    for day in dates:
        wrk_days = cal.bizdays(day, maturity)
        yield_r = b3.interpolate(wrk_days, curves_lists[dates_index], curves_dics[dates_index])
        historic.append(yield_r)
        dates_index += 1

    graph.plot(dates_str, historic)
    graph.title(maturity_str.upper())
    graph.xticks(rotation=45)
    graph.grid()
    graph.gcf().set_size_inches(15*len(dates)/34, 8)