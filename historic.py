# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 17:41:04 2020

@author: buzon
"""

import matplotlib.pyplot as graph
import B3curve as b3
from datetime import datetime, timedelta
from bizdays import Calendar
import di_derivative as di

FERIADOS = open('C:/Users/buzon/Documents/Python/Arquivos base/Anbima.txt', 'r')
HOLIDAYS = []
for linha in FERIADOS:
    HOLIDAYS.append(linha.strip())
FERIADOS.close()
cal = Calendar(HOLIDAYS, ['Sunday', 'Saturday'])

PATH = 'C:/Users/buzon/Documents/Curvas/'

SEP = '@'
NEXT_DAY = 1

INDEX = 'pre'
FORMAT = '%d%m%Y'
FORMAT_B3 = '%Y%m%d'

def historic_b3(start, end, maturity_str):
    """Get the historic yield of a vertice. Format ddmmyyyy"""

    start_dt = datetime.strptime(start, FORMAT)
    end_dt = datetime.strptime(end, FORMAT)
    
    curves_dics = []
    curves_lists = []
    dates_str = []
    dates = []
    
    while start_dt <= end_dt:
        start_str = datetime.strftime(start_dt, FORMAT_B3)
        curve_list = b3.get_curve_b3(start_str, INDEX)
        curve_dic = b3.get_dic_curve(curve_list)
        dates.append(start_dt)
        dates_str.append(start_str)
        curves_dics.append(curve_dic)
        curves_lists.append(curve_dic)
        start_dt = cal.offset(start_dt, NEXT_DAY)
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

def save_curve_txt(start, end=None):
    """Save the B3 yield Curve to a txt file. Format ddmmyyyy"""

    start_dt = cal.adjust_next(datetime.strptime(start, FORMAT))
    if end != None:
        end_dt = cal.adjust_next(datetime.strptime(end, FORMAT))
    else:
        end_dt = start_dt
        
    while start_dt <= end_dt:
        start_str = datetime.strftime(start_dt, FORMAT_B3)
        curve_list = b3.get_curve_b3(start_str, INDEX)
        file_name = 'Curve_' + start_str + '.txt'
        try:
            curve_txt = open(PATH + file_name, 'r')
            curve_txt.close()
            print('File {} already exist.'.format(file_name))
        except:
            curve_txt = open(PATH + file_name, 'w')
            for line in curve_list:
                curve_txt.write(str(line[0])+'@'+str(line[1]) + '\n')
            curve_txt.close()
            print('File {} saved.'.format(file_name))     
        start_dt = cal.offset(start_dt, NEXT_DAY)
        # start_dt = datetime(start_dt.year, start_dt.month, start_dt.day)

def historic_txt(start, end, maturity_str):
    """Get the historic yield of a vertice. Format ddmmyyyy"""

    start_dt = datetime.strptime(start, FORMAT)
    end_dt = datetime.strptime(end, FORMAT)
    
    error = False
    curves_dics = []
    curves_lists = []
    dates_str = []
    dates = []
    
    while start_dt <= end_dt:
        start_str = datetime.strftime(start_dt, FORMAT_B3)
        file_name = 'Curve_' + start_str + '.txt'
        curve_txt = open(PATH + file_name, 'r')

        curve_list = []
        for i in curve_txt:
            i_list = i.split(SEP)
            i_list[0] = int(i_list[0])
            i_list[1] = float(i_list[1].strip())
            curve_list.append(i_list)
        if curve_list != []:
            curve_dic = b3.get_dic_curve(curve_list)
            dates.append(start_dt)
            dates_str.append(start_str)
            curves_dics.append(curve_dic)
            curves_lists.append(curve_list)
            start_dt = cal.offset(start_dt, NEXT_DAY)
            start_dt = datetime(start_dt.year, start_dt.month, start_dt.day)
        else:
            print('Curve {} is empty.'.format(start_str))
            error = True
            start_dt = end_dt + timedelta(1)
        
        curve_txt.close()
    
    if not error:
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
        
        delta = int(round((historic[len(historic)-1] - historic[0])*100, 0))
        if delta > 0:
            text = '{} increased +{} bps.'
        elif delta < 0:
            text = '{} decreased -{} bps.'
        else:
            text = '{} has {} delta.'
            
        print(text.format(maturity_str.upper(), str(abs(delta))))

def get_cls_yield(maturity, curve_date=None):
    """Get the close yield given the maturity of di future. Format: YYYYMMDD"""
    if curve_date == None:
        curve_dt = cal.adjust_previous(datetime.today() + timedelta(-1))
        date_str = datetime.strftime(curve_dt, FORMAT_B3)
    else:
        curve_dt = datetime.strptime(curve_date, FORMAT)
        date_str = curve_date
    maturity = di.get_maturity(maturity)
    curve = b3.get_curve_txt(date_str)
    curve_dic = b3.get_dic_curve(curve)
    wrk_days = cal.bizdays(curve_dt, maturity)
    cls_yield = b3.interpolate(wrk_days, curve, curve_dic)
    
    return cls_yield
