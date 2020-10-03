# -*- coding: utf-8 -*-
"""
Created on Wed Sep  9 00:03:18 2020

@author: Buzoni
"""

from datetime import timedelta, date, datetime
from bizdays import Calendar
import B3curve
import di_derivative as di
import historic as hist

FERIADOS = open('C:/Users/buzon/Documents/Python/Arquivos base/Anbima.txt', 'r')
HOLIDAYS = []
for linha in FERIADOS:
    HOLIDAYS.append(linha.strip())
FERIADOS.close()

FORMAT = '%Y%m%d'

#Holidays and settlement date.
cal = Calendar(HOLIDAYS, ['Sunday', 'Saturday'])
dt_today = date.today()
dt_stlm = cal.adjust_previous(date.today()+timedelta(-1))
curve_date = datetime.strftime(dt_stlm, FORMAT)
INDEX_B3 = 'pre'

#Yield Curve
curve_list = B3curve.get_curve_b3(curve_date, INDEX_B3)
curve_dic = B3curve.get_dic_curve(curve_list)

def create_cash_flow(maturity_years, pmt_per_year, stlm=dt_stlm):
    """"Create a cash flow given a number of years to maturity and
    how many payments per year. Set pmt_per_year = 0 to bullet cash flow"""
    cash_flow = []
    maturity = cal.adjust_next(cal.offset(stlm, 252 * maturity_years).replace(day=stlm.day))
    if pmt_per_year == 0:
        cash_flow.append(maturity)
    else:
        days_between_pmt = int(round(252 / pmt_per_year, 0))
        while maturity > stlm:
            cash_flow.append(maturity)
            maturity = cal.adjust_next(cal.offset(maturity, -days_between_pmt)
                                       .replace(day=stlm.day))
    return cash_flow

def payments(principal, inter_rate, maturity_years, amortization_year, interests_year):
    """Return my cash flow with the value of amortizations and interests payments
    Set amortization_year and interest_year to 0 for bullet cash flow"""
    payment = []
    inter_rate /= 100
    inter_rate_period = (1 + inter_rate)**(1 / interests_year) - 1
    pmts = max(amortization_year, interests_year)
    cash_flow = create_cash_flow(maturity_years, pmts)
    ratio = interests_year / amortization_year
    interests = principal * inter_rate_period
    amortization = principal / (amortization_year * maturity_years)
    for pmt in range(1, len(cash_flow) + 1):
        payment_r = []
        if pmt % ratio == 0:
            payment_r.append(cash_flow[pmt - 1])
            payment_r.append(round(interests + amortization, 2))
        else:
            payment_r.append(cash_flow[pmt - 1])
            payment_r.append(round(interests, 2))
        payment.append(payment_r)
    return payment

def total(cash_flow):
    """Just return the sum of interests and amortization"""
    sum_pmt = 0
    for pmts in cash_flow:
        sum_pmt += pmts
    return sum_pmt

def dv01(future_value, maturity, yield_m, dt_st=dt_stlm):
    """Return the dv01"""
    wrk_days = cal.bizdays(dt_st, maturity)
    yield_m /= 100
    yield_s = yield_m + 0.0001
    present_vl = future_value/((1+yield_m)^(wrk_days/252))
    present_vls = future_value/((1+yield_s)^(wrk_days/252))
    return present_vls - present_vl

def sep_matrix(matrix):
    """Separate the nx2 matrix in two lists."""
    list_1 = []
    list_2 = []
    for value in matrix:
        list_1.append(value[0])
        list_2.append(value[1])
    return list_1, list_2

def get_str_date(str_list):
    """Input a list with string dates in format yyyymmdd"""
    new_list = []
    for date_str in str_list:
        date_str = di.get_maturity(date_str)
        new_list.append(date_str)
    return new_list

def tweek(list_tweek, single_list, fv_list=None):
    """Tweek the dv01.
    Here, you can input a nx2 matrix with the maturities in first column
    and the FV in second column. Or you can also input two separate lists.
    Single_list is the list of maturities and fv_list is the FV list
    You can input a list with di BBG or BM&F maturity codes as tweek_list"""
    r_list = []
    for value in list_tweek:
        r_list.append(0)
    #Separating the matrix.
    if fv_list is None:
        r_tuple = sep_matrix(single_list)
        single_list = r_tuple[0]
        fv_list = r_tuple[1]
    #Turning the elements of list_tweek into dates.
    if isinstance(list_tweek[0], str):
        list_tweek = get_str_date(list_tweek)
    #Turning the elements of single_list into dates.
    if isinstance(single_list[0], str):
        single_list = get_str_date(single_list)
    if len(single_list) == len(fv_list):
        #The hard code.
        fv_index = 0
        for value in single_list:
            tweek_index = 0
            future_value = fv_list[fv_index]
            while value > list_tweek[tweek_index]:
                tweek_index += 1
                if tweek_index == len(list_tweek):
                    tweek_index -= 1
                    break
            if tweek_index == 0 and value < list_tweek[0]:
                next_date = list_tweek[tweek_index]
                prev_date = next_date
            elif tweek_index == len(list_tweek) - 1 and value > list_tweek[tweek_index]:
                prev_date = list_tweek[tweek_index - 1]
                next_date = prev_date
            else:
                next_date = list_tweek[tweek_index]
                prev_date = list_tweek[tweek_index - 1]
            if value < next_date:
                days_to_next_date = cal.bizdays(value, next_date)
            else:
                days_to_next_date = cal.bizdays(next_date, value)
            if value > prev_date:
                days_to_prev_date = cal.bizdays(prev_date, value)
            else:
                days_to_prev_date = cal.bizdays(value, prev_date)
            total_days = days_to_next_date + days_to_prev_date
            prop_next = 1 - days_to_next_date / total_days
            prop_prev = 1 - days_to_prev_date / total_days
            value_to_next = future_value * prop_next
            value_to_prev = future_value * prop_prev
            if tweek_index == 0:
                r_list[tweek_index] += value_to_next
                r_list[tweek_index] += value_to_prev
            elif tweek_index == len(list_tweek):
                r_list[tweek_index - 1] += value_to_next
                r_list[tweek_index - 1] += value_to_prev
            else:
                r_list[tweek_index] += value_to_next
                r_list[tweek_index - 1] += value_to_prev
            fv_index += 1            
        return r_list
    #If the lists have diferents sizes, we return this warning:
    else:
        return print('Lists have not the same size.')

def ncontracts_gdv(maturity, dv01):
    """Get the number of contract given the dv01"""
    cls_yield = hist.get_cls_yield(maturity)
    dv_per_ct = di.dv_di(maturity, 1, cls_yield)
    return int(round(dv01 / dv_per_ct, 0))

def hedge_di(list_di, list_expo):
    """Calculate the di contracts to make the hedge of a given cash flow"""
    list_r = []
    if len(list_di) == len(list_expo):
        for index, value in enumerate(list_di):
            list_r.append([value, -ncontracts_gdv(value, list_expo[index])])
    else:
        list_r = print("The lists have not the same size.")
    return list_r
    
